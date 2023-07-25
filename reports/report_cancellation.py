# -*- coding: utf-8 -*-
import sys

sys.path.append('../')

import pandas as pd
from impala.dbapi import connect
import importlib
import re
from routines.send_mail import send_mail

cfg = importlib.import_module('.cfg', 'config')


def send_cancellation(reportType=None):
    impala_con = connect(host=cfg.impala_host)
    impala_cur = impala_con.cursor()
    proc_date = ''
    if reportType == 'new':
        query = 'select max(proc_date) from ipv_db.ca_tm_trademark'
        impala_cur.execute(query)
        data = impala_cur.fetchall()
        proc_date = data[0][0]

        query = "select status from etl_db.reports_status where proc_date='{}' and report_name='report_cancellation'".format(
            proc_date)

        impala_cur.execute(query)
        data = impala_cur.fetchall()
        status = data[0][0]

        if status == 1:
            print('no new data uploaded, skip')
            return

    impala_cur.execute('DROP TABLE IF EXISTS ipv_db.tmp1;')
    impala_cur.execute('DROP TABLE IF EXISTS ipv_db.tmp2;')
    impala_cur.execute('CREATE TABLE IF NOT EXISTS ipv_db.tmp1 (st13applicationnumber bigint,proc_date string);')
    impala_cur.execute('CREATE TABLE IF NOT EXISTS ipv_db.tmp2 (st13applicationnumber bigint,markeventdate string);')
    query0 = """
              insert into ipv_db.tmp1
              select distinct tm.st13applicationnumber,tm.proc_date
              from ipv_db.ca_tm_trademark tm left outer join ipv_db.ca_tm_applicant app
              on
              tm.st13applicationnumber=app.st13applicationnumber and tm.proc_date=app.proc_date
              left outer join ipv_db.ca_tm_national_trademark_information nti
              on
              tm.st13applicationnumber=nti.st13applicationnumber and tm.proc_date=nti.proc_date
              right join (
                         select st13applicationnumber,max(proc_date) proc_date
                         from ipv_db.ca_tm_trademark 
                         group by st13applicationnumber
                         order by st13applicationnumber
                        ) AS newrecord on (tm.st13applicationnumber = newrecord.st13applicationnumber and tm.proc_date = newrecord.proc_date) 
              where app.nationallegalentitycode='CA'
              and nti.markcurrentstatusinternaldescriptiontext= 'Registered'
              and app.st13applicationnumber not in (select r.st13applicationnumber from ipv_db.ca_tm_national_representative r)
              
            """
    impala_cur.execute(query0)

    query1 = """
             insert into ipv_db.tmp2
             select a.st13applicationnumber,max(b.markeventdate)
             from ipv_db.tmp1 a 
             inner join ( select cp.st13applicationnumber,cp.proc_date,cpe.markeventdate
                          from ipv_db.ca_tm_cancellation_proceedings cp 
                          right join ipv_db.ca_tm_cancellationproceeding_events cpe 
                          on (cp.st13applicationnumber = cpe.st13applicationnumber and cp.proc_date = cpe.proc_date and cp.legalproceedingidentifier = cpe.legalproceedingidentifier and cp.proceedingstagecode =cpe.proceedingstagecode) 
                        ) AS b on a.st13applicationnumber=b.st13applicationnumber and a.proc_date=b.proc_date
             right join (
                        select st13applicationnumber,max(proc_date) proc_date
                        from ipv_db.ca_tm_trademark 
                        group by st13applicationnumber
                       ) AS newrecord on (a.st13applicationnumber = newrecord.st13applicationnumber and a.proc_date = newrecord.proc_date) 
             group by a.st13applicationnumber
             """
    impala_cur.execute(query1)

    query3 = """
             select lower(entityname) from ipv_db.mailer_blacklist where entityname is not NULL;
             """
    impala_cur.execute(query3)
    data = impala_cur.fetchall()
    df_blacklistName = pd.DataFrame(data)
    df_blacklistName.columns = ['entityname_bl']

    query2 = """
    select distinct 'REGISTERED' as MailerType,a.st13applicationnumber,substr(cast(a.st13applicationnumber as string),7,7) as Fileid
    ,substr(cast(a.st13applicationnumber as string),14,2) as ExtensionCounter
    ,CASE
    
    WHEN c.applicationlanguagecode = 'en' AND (int_months_between(b.markeventresponsedate,NOW()) BETWEEN 0 AND 2) THEN 'UX45_3_E_1'
    WHEN c.applicationlanguagecode = 'fr' AND (int_months_between(b.markeventresponsedate,NOW()) BETWEEN 0 AND 2) THEN 'UX45_3_F_1'
    WHEN c.applicationlanguagecode = 'en' AND (int_months_between(b.markeventresponsedate,NOW()) BETWEEN 3 AND 4) THEN 'UX45_2_E_1'
    WHEN c.applicationlanguagecode = 'fr' AND (int_months_between(b.markeventresponsedate,NOW()) BETWEEN 3 AND 4) THEN 'UX45_2_F_1'
    WHEN c.applicationlanguagecode = 'en' AND (int_months_between(b.markeventresponsedate,NOW()) >= 5) THEN 'UX45_1_E_1'
    WHEN c.applicationlanguagecode = 'fr' AND (int_months_between(b.markeventresponsedate,NOW()) >- 5) THEN 'UX45_1_F_1'
    ELSE ''
    END as CardType
    ,d.legalentityname,d.addresslinetext1,d.addresslinetext2,d.geographicregionname,d.countrycode,d.postalcode
    ,CASE
    when e.marksignificantverbalelementtext='-' then concat('TM: ' , substr(cast(a.st13applicationnumber as string),7,7) , ' - ' , ISNULL(f.indexheadingtext1,''))
    else concat('TM: ' , substr(cast(a.st13applicationnumber as string),7,7) , ' - ' , ISNULL(e.marksignificantverbalelementtext,''))
    END as Text1_TMNumber
    ,CASE
    WHEN c.applicationlanguagecode = 'en' THEN 'STATUS: REGISTERED'
    WHEN c.applicationlanguagecode = 'fr' THEN 'STATUS: ENREGISTRÉE'
    END as Text2_Status
    ,CASE
    WHEN c.applicationlanguagecode = 'en' THEN concat("CIPO RESPONSE DEADLINE: ",from_unixtime(unix_timestamp(b.markeventresponsedate),'MMM'),' ',from_unixtime(unix_timestamp(b.markeventresponsedate),'dd'),' ',from_unixtime(unix_timestamp(b.markeventresponsedate),'yyyy'))
    
    WHEN c.applicationlanguagecode = 'fr' THEN concat("DATE LIMITE DE RÉPONSE DE L'OPIC: ",from_unixtime(unix_timestamp(b.markeventresponsedate),'MMM'),' ',from_unixtime(unix_timestamp(b.markeventresponsedate),'dd'),' ',from_unixtime(unix_timestamp(b.markeventresponsedate),'yyyy'))
    END as Text4
    ,b.markeventdescriptiontext
    ,c.proc_date,b.*
    
    --,markeventdescriptiontext,a.markeventdate,b.markeventresponsedate
    from ipv_db.tmp2 a 
    inner join ( select cp.*,cpe.markeventcategory,cpe.markeventresponsedate,cpe.markeventcode,cpe.markeventdescriptiontext,cpe.markeventdescriptiontext_fr,cpe.markeventadditionaltext,cpe.markeventdate
                 from ipv_db.ca_tm_cancellation_proceedings cp 
                 right join ipv_db.ca_tm_cancellationproceeding_events cpe 
                 on (cp.st13applicationnumber = cpe.st13applicationnumber and cp.proc_date = cpe.proc_date and cp.legalproceedingidentifier = cpe.legalproceedingidentifier and cp.proceedingstagecode =cpe.proceedingstagecode) 
               ) AS b 
    on
    a.st13applicationnumber=b.st13applicationnumber and a.markeventdate=b.markeventdate
    left outer join ipv_db.ca_tm_trademark c
    on
    a.st13applicationnumber=c.st13applicationnumber
    left outer join ipv_db.ca_tm_applicant d
    on
    a.st13applicationnumber=d.st13applicationnumber
    left outer join ipv_db.ca_tm_markrepresentation e
    on
    a.st13applicationnumber=e.st13applicationnumber
    left outer join ipv_db.ca_tm_index_heading f
    on
    a.st13applicationnumber=f.st13applicationnumber
    
    where markeventresponsedate<>'-' and markeventresponsedate<>' '
    and c.proc_date=(select max(cc.proc_date) from ipv_db.ca_tm_trademark cc where cc.st13applicationnumber=c.st13applicationnumber)
    and b.proc_date=(select max(bb.proc_date) from ipv_db.ca_tm_cancellation_proceedings bb where bb.st13applicationnumber=b.st13applicationnumber)
    and d.proc_date=(select max(dd.proc_date) from ipv_db.ca_tm_applicant dd where dd.st13applicationnumber=d.st13applicationnumber)
    and e.proc_date=(select max(ee.proc_date) from ipv_db.ca_tm_markrepresentation ee where ee.st13applicationnumber=e.st13applicationnumber)
    and f.proc_date=(select max(ff.proc_date) from ipv_db.ca_tm_index_heading ff where ff.st13applicationnumber=f.st13applicationnumber)
    and b.markeventresponsedate>NOW()
    and a.st13applicationnumber not in (select distinct st13applicationnumber from ipv_db.mailer_blacklist where st13applicationnumber is not NULL) 
    and b.proceedingstagecode = '312'
    and b.markeventdescriptiontext like 'Deadline%'
    order by a.st13applicationnumber
             """
    # print(query2)
    impala_cur.execute(query2)
    data = impala_cur.fetchall()
    df_data = pd.DataFrame(data)
    # print(df_data.shape)
    df_data.columns = ['mailertype', 'st13applicationnumber', 'fileid', 'extensioncounter', 'cardtype',
                       'legalentityname', 'addresslinetext1', 'addresslinetext2', 'geographicregionname', 'countrycode',
                       'postalcode', 'text1_tmnumber', 'text2_status', 'text4', 'Text 5 - markeventdescriptiontext',
                       'proc_date', 'st13applicationnumber', 'proc_date', 'legalproceedingidentifier',
                       'proceedingstagecode', 'proceedingstagedescriptiontext_en', 'proceedingstagedescriptiontext_fr',
                       'legalproceedingfilingdate', 'oppositioncasetypedescription_en',
                       'oppositioncasetypedescription_fr', 'nationalstatuscategory', 'nationalstatuscode',
                       'nationalstatusdate', 'nationalstatusinternaldescriptiontext',
                       'Text 3  - plaintiff_legalentityname', 'plaintiff_entityname', 'plaintiff_addresslinetext1',
                       'plaintiff_addresslinetext2', 'plaintiff_addresslinetext3', 'plaintiff_geographicregionname',
                       'plaintiff_countrycode', 'plaintiff_postalcode', 'plaintiff_cor_entityname',
                       'plaintiff_cor_addresslinetext1', 'plaintiff_cor_addresslinetext2',
                       'plaintiff_cor_addresslinetext3', 'plaintiff_cor_geographicregionname',
                       'plaintiff_cor_countrycode', 'plaintiff_cor_postalcode', 'plaintiff_rep_commenttext',
                       'plaintiff_rep_entityname', 'plaintiff_rep_addresslinetext1', 'plaintiff_rep_addresslinetext2',
                       'plaintiff_rep_addresslinetext3', 'plaintiff_rep_geographicregionname',
                       'plaintiff_rep_countrycode', 'plaintiff_rep_postalcode', 'defendant_entityname',
                       'defendant_addresslinetext1', 'defendant_addresslinetext2', 'defendant_addresslinetext3',
                       'defendant_geographicregionname', 'defendant_countrycode', 'defendant_postalcode',
                       'defendant_cor_commenttext', 'defendant_cor_entityname', 'defendant_cor_addresslinetext1',
                       'defendant_cor_addresslinetext2', 'defendant_cor_addresslinetext3',
                       'defendant_cor_geographicregionname', 'defendant_cor_countrycode', 'defendant_cor_postalcode',
                       'defendant_rep_commenttext', 'defendant_rep_entityname', 'defendant_rep_addresslinetext1',
                       'defendant_rep_addresslinetext2', 'defendant_rep_addresslinetext3',
                       'defendant_rep_geographicregionname', 'defendant_rep_countrycode', 'defendant_rep_postalcode',
                       'markeventcategory', 'markeventresponsedate', 'markeventcode', 'markeventdescriptiontext',
                       'markeventdescriptiontext_fr', 'markeventadditionaltext', 'markeventdate']
    # print(df_data.shape)
    # df_data['entityname_lower'] = df_data['legalentityname'].str.lower()
    df_data = df_data.loc[:,
              ['mailertype', 'st13applicationnumber', 'fileid', 'extensioncounter', 'cardtype', 'legalentityname',
               'addresslinetext1', 'addresslinetext2', 'geographicregionname', 'countrycode', 'postalcode',
               'text1_tmnumber', 'text2_status', 'Text 3  - plaintiff_legalentityname', 'text4', 'text5', 'proc_date',
               'st13applicationnumber', 'proc_date', 'legalproceedingidentifier', 'proceedingstagecode',
               'proceedingstagedescriptiontext_en', 'proceedingstagedescriptiontext_fr', 'legalproceedingfilingdate',
               'oppositioncasetypedescription_en', 'oppositioncasetypedescription_fr', 'nationalstatuscategory',
               'nationalstatuscode', 'nationalstatusdate', 'nationalstatusinternaldescriptiontext',
               'plaintiff_entityname', 'plaintiff_addresslinetext1', 'plaintiff_addresslinetext2',
               'plaintiff_addresslinetext3', 'plaintiff_geographicregionname', 'plaintiff_countrycode',
               'plaintiff_postalcode', 'plaintiff_cor_entityname', 'plaintiff_cor_addresslinetext1',
               'plaintiff_cor_addresslinetext2', 'plaintiff_cor_addresslinetext3', 'plaintiff_cor_geographicregionname',
               'plaintiff_cor_countrycode', 'plaintiff_cor_postalcode', 'plaintiff_rep_commenttext',
               'plaintiff_rep_entityname', 'plaintiff_rep_addresslinetext1', 'plaintiff_rep_addresslinetext2',
               'plaintiff_rep_addresslinetext3', 'plaintiff_rep_geographicregionname', 'plaintiff_rep_countrycode',
               'plaintiff_rep_postalcode', 'defendant_entityname', 'defendant_addresslinetext1',
               'defendant_addresslinetext2', 'defendant_addresslinetext3', 'defendant_geographicregionname',
               'defendant_countrycode', 'defendant_postalcode', 'defendant_cor_commenttext', 'defendant_cor_entityname',
               'defendant_cor_addresslinetext1', 'defendant_cor_addresslinetext2', 'defendant_cor_addresslinetext3',
               'defendant_cor_geographicregionname', 'defendant_cor_countrycode', 'defendant_cor_postalcode',
               'defendant_rep_commenttext', 'defendant_rep_entityname', 'defendant_rep_addresslinetext1',
               'defendant_rep_addresslinetext2', 'defendant_rep_addresslinetext3', 'defendant_rep_geographicregionname',
               'defendant_rep_countrycode', 'defendant_rep_postalcode', 'markeventcategory', 'markeventresponsedate',
               'markeventcode', 'markeventdescriptiontext', 'markeventdescriptiontext_fr', 'markeventadditionaltext',
               'markeventdate']]
    df_final = df_data
    # print(df_final.shape)
    # df_final['drop'] = 0
    # for x,row in df_final.iterrows():
    #    for b in df_blacklistName['entityname_bl'].unique():
    #        if row['entityname_lower'] in b: 
    #            print(x,row['entityname_lower'],b)
    #            df_final.loc[x,'drop'] =1
    #            break
    #        elif b in row['entityname_lower']:
    #            if len(b.split()) == 1:
    #                if b+' ' in row['entityname_lower']:
    #                    pass
    #                elif ' '+b in row['entityname_lower']:
    #                    pass
    #                else:
    #                    continue
    #
    #            print(x,row['entityname_lower'],b)
    #            df_final.loc[x,'drop'] =1
    #            break
    # df_final = df_final[df_final['drop']==0]
    # df_final = df_final.drop('drop',axis=1)
    # df_final = df_final.drop('entityname_lower',axis=1)
    # print(len(df_final))
    # get city
    postcode_list = ''
    for p_no, p in enumerate(df_final['postalcode'].values):
        if p_no == len(df_final) - 1:
            postcode_list += '"' + p + '"'
        else:
            postcode_list += '"' + p + '",'
    query4 = """
             select * from ipv_db.city_postcode where postcode in ({});
             """.format(postcode_list)
    impala_cur.execute(query4)
    data1 = impala_cur.fetchall()
    df_city = pd.DataFrame(data1)
    df_city.columns = ['county', 'postcode', 'city', 'state']
    df_final = df_final.merge(df_city[['postcode', 'city']], how='left', left_on='postalcode', right_on='postcode')
    df_final = df_final.drop('postcode', axis=1)
    print(df_final.shape)
    # df_final = df_final.loc[:,['mailertype','st13applicationnumber','fileid','extensioncounter','cardtype','legalentityname','addresslinetext1','addresslinetext2','city','geographicregionname','countrycode','postalcode','text1_tmnumber','text2_status','text3','proc_date']]
    for i, row in df_final.iterrows():
        if row['city'] == '' or pd.isnull(row['city']): continue
        tmp_str = re.sub('Montr\\xc3\\xa9al', 'Montreal', row['addresslinetext2'])
        tmp_str = re.sub('Qu\\xc3\\xa9bec', 'Quebec', tmp_str)
        if re.search(row['city'], tmp_str, re.IGNORECASE):
            # print(i, row['addresslinetext2'], row['city'])
            extra_string = re.sub(row['city'].lower() + '[\,]?', '', tmp_str.lower()).strip()
            if extra_string == '':
                df_final.loc[i, 'addresslinetext2'] = row['city']
                # print('1:',i, row['addresslinetext2'], row['city'])
            else:
                extra_string = re.sub(row['city'] + '[\,]?', '', tmp_str).strip()
                df_final.loc[i, 'addresslinetext1'] += ', ' + extra_string
                df_final.loc[i, 'addresslinetext2'] = row['city']
                # print('2:',i, row['addresslinetext2'], row['city'])
            pass
        else:
            # print(i, row['addresslinetext2'], row['city'])
            df_final.loc[i, 'addresslinetext1'] += ', ' + df_final.loc[i, 'addresslinetext2']
            df_final.loc[i, 'addresslinetext2'] = row['city']

    df_final = df_final.drop('city', axis=1)
    writer = pd.ExcelWriter('report_cancellation.xlsx', engine='openpyxl')
    df_final.to_excel(writer, index=None)
    writer.save()
    #############################################################################
    # Get credential for EMail notification
    #############################################################################
    # CIPO Unrepresented - Searched Report: October 2020
    td = pd.to_datetime('today')

    def get_mail_params(rfile):
        mail_params = cfg.mail_params

        var_params = {
            'text': '',
            'subject': 'CIPO Unrepresented - Cancellation Report: {} {}'.format(td.strftime("%B"), td.strftime("%Y")),
            'attach_file': rfile,
        }

        mail_params.update(var_params)

        return mail_params

    send_mail(get_mail_params('report_cancellation.xlsx'))
    print('email sent')

    query = "update etl_db.reports_status set status=1 where proc_date='{}' and report_name='report_cancellation'".format(
        proc_date)
    impala_cur.execute(query)


if __name__ == "__main__":
    try:
        print('=' * 30)
        print('Getting CIPO Unrepresented - Cancellation Report')
        print('=' * 30)
        try:
            send_cancellation(sys.argv[1])
        except:
            send_cancellation()

    except Exception as err:
        print('fail')
        print(err)
