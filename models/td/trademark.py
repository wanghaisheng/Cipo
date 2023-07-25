import importlib
helpers = importlib.import_module('.helpers', 'models')

######################################################################
#
######################################################################
table  = 'ca_tm_trademark'
body   =   ('(ST13ApplicationNumber BIGINT,'
            'proc_date STRING,'
            'RequestExaminationCategory STRING,'
            'RegistrationOfficeCode STRING,'
            'ReceivingOfficeCode STRING,'
            'ReceivingOfficeDate STRING,'
            'IPOfficeCode STRING,'
            'RegistrationNumber STRING,'   
            'ApplicationDate STRING,'                     
            'RegistrationDate STRING,'                     
            'FilingPlace STRING,'                     
            'ApplicantFileReference STRING,'
            'ApplicationLanguageCode STRING,'
            'ExpiryDate STRING,'                     
            'TerminationDate STRING,'               
            'MarkCurrentStatusCode STRING,'
            'AssociationCategory STRING,'
            'Associated_IPOfficeCode STRING,'
            'Associated_ST13ApplicationNumber STRING,'
            'Divisional_IPOfficeCode STRING,'
            'Divisioanl_ST13ApplicationNumber STRING,'
            'Divisioanl_InitialApplicationDate STRING,'
            'InternationalMarkIdentifier STRING,'
            'MarkCurrentStatusDate STRING,'
            'MarkCategory STRING,'            
            'MarkDisclaimerText_en STRING,'
            'MarkDisclaimerText_fr STRING,'
            'NonUseCancelledIndicator STRING,'
            'TradeDistinctivenessIndicator STRING,'            
            'TradeDistinctivenessText STRING,'            
            'UseLimitationText STRING,'
            'CommentText STRING,'
            'OppositionPeriodStartDate STRING,'
            'OppositionPeriodEndDate STRING,'
            'PRIMARY KEY(ST13ApplicationNumber,proc_date)) PARTITION BY HASH(ST13ApplicationNumber) PARTITIONS 12 STORED AS KUDU ')

body_ext = ('(ST13ApplicationNumber BIGINT,'
            'proc_date STRING,'
            'RequestExaminationCategory STRING,'
            'RegistrationOfficeCode STRING,'
            'ReceivingOfficeCode STRING,'
            'ReceivingOfficeDate STRING,'
            'IPOfficeCode STRING,'
            'RegistrationNumber STRING,'   
            'ApplicationDate STRING,'                     
            'RegistrationDate STRING,'                     
            'FilingPlace STRING,'                     
            'ApplicantFileReference STRING,'
            'ApplicationLanguageCode STRING,'
            'ExpiryDate STRING,'                     
            'TerminationDate STRING,'               
            'MarkCurrentStatusCode STRING,'
            'AssociationCategory STRING,'
            'Associated_IPOfficeCode STRING,'
            'Associated_ST13ApplicationNumber STRING,'
            'Divisional_IPOfficeCode STRING,'
            'Divisioanl_ST13ApplicationNumber STRING,'
            'Divisioanl_InitialApplicationDate STRING,'
            'InternationalMarkIdentifier STRING,'
            'MarkCurrentStatusDate STRING,'
            'MarkCategory STRING,'            
            'MarkDisclaimerText_en STRING,'
            'MarkDisclaimerText_fr STRING,'
            'NonUseCancelledIndicator STRING,'
            'TradeDistinctivenessIndicator STRING,'            
            'TradeDistinctivenessText STRING,'            
            'UseLimitationText STRING,'
            'CommentText STRING,'
            'OppositionPeriodStartDate STRING,'
            'OppositionPeriodEndDate STRING) ')             

model = helpers.tbl_model(table, [body, body_ext])
