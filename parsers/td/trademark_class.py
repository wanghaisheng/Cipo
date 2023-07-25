#############################################################################
# Extract assignee data from Assignment XML file
#############################################################################
import xml.etree.ElementTree as ET
import importlib
helpers = importlib.import_module('.helpers', 'parsers')

#############################################################################
def create_line(xml_part):
    
    ns = {'tmk':'http://www.wipo.int/standards/XMLSchema/ST96/Trademark',
          'com':'http://www.wipo.int/standards/XMLSchema/ST96/Common',
          'catmk':'http://www.cipo.ic.gc.ca/standards/XMLSchema/ST96/Trademark',
          'cacom':'http://www.cipo.ic.gc.ca/standards/XMLSchema/ST96/Common'

         }
    to_extract = [".//tmk:TrademarkBag/tmk:Trademark/com:ApplicationNumber/com:ST13ApplicationNumber"]

    parts_tag = './/tmk:TrademarkBag/tmk:Trademark/tmk:NationalTrademarkInformation/catmk:TrademarkClass'

    sub_tags = ['.//catmk:TrademarkClassCode',
                './/catmk:TrademarkClassDescriptionBag/catmk:TrademarkClassDescription[@com:languageCode="en"]',
                './/catmk:TrademarkClassDescriptionBag/catmk:TrademarkClassDescription[@com:languageCode="fr"]' 
               ]


    return helpers.td_extract(xml_part, to_extract, ns, parts_tag, sub_tags)

