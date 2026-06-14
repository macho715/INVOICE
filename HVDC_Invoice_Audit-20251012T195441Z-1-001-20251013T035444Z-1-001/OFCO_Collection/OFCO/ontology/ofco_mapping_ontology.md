# OFCO Mapping Ontology (HVDC_MAPPING_SYSTEM_GUIDE v2.6)

본 파일은 OFCO 매핑 규칙을 RDF/OWL Turtle 형식으로 정의한 온톨로지입니다.

```turtle
@prefix hvdc: <http://example.com/hvdc#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

hvdc:MappingRule a rdfs:Class .
hvdc:CostCenter a rdfs:Class .

hvdc:priority a rdf:Property ; rdfs:domain hvdc:MappingRule ; rdfs:range xsd:int .
hvdc:regexPattern a rdf:Property ; rdfs:domain hvdc:MappingRule ; rdfs:range xsd:string .
hvdc:mapsToCostCenterA a rdf:Property ; rdfs:domain hvdc:MappingRule ; rdfs:range hvdc:CostCenter .
hvdc:mapsToCostCenterB a rdf:Property ; rdfs:domain hvdc:MappingRule ; rdfs:range hvdc:CostCenter .

hvdc:AT_COST a hvdc:CostCenter ; rdfs:label "AT COST" .
hvdc:AT_COSTCONSUMABLES a hvdc:CostCenter ; rdfs:label "AT COST(CONSUMABLES)" .
hvdc:AT_COSTFOLKLIFT a hvdc:CostCenter ; rdfs:label "AT COST(FOLKLIFT)" .
hvdc:AT_COSTFUEL_SUPPLY_10000GL a hvdc:CostCenter ; rdfs:label "AT COST(FUEL SUPPLY (10,000GL))" .
hvdc:AT_COSTWATER_SUPPLY a hvdc:CostCenter ; rdfs:label "AT COST(WATER SUPPLY)" .
hvdc:CONTRACT a hvdc:CostCenter ; rdfs:label "CONTRACT" .
hvdc:CONTRACTAF_FOR_BA a hvdc:CostCenter ; rdfs:label "CONTRACT(AF FOR BA)" .
hvdc:CONTRACTAF_FOR_CC a hvdc:CostCenter ; rdfs:label "CONTRACT(AF FOR CC)" .
hvdc:CONTRACTAF_FOR_EQUIP_PASS_ARRG a hvdc:CostCenter ; rdfs:label "CONTRACT(AF FOR EQUIP PASS ARRG)" .
hvdc:CONTRACTAF_FOR_FW_SA a hvdc:CostCenter ; rdfs:label "CONTRACT(AF FOR FW SA)" .
hvdc:CONTRACTAF_FOR_PASS_ARRG a hvdc:CostCenter ; rdfs:label "CONTRACT(AF FOR PASS ARRG)" .
hvdc:CONTRACTAF_FOR_PTW_ARRG a hvdc:CostCenter ; rdfs:label "CONTRACT(AF FOR PTW ARRG)" .
hvdc:CONTRACTOFCO_FOLK_LIFT_HF a hvdc:CostCenter ; rdfs:label "CONTRACT(OFCO FOLK LIFT HF)" .
hvdc:CONTRACTOFCO_HF a hvdc:CostCenter ; rdfs:label "CONTRACT(OFCO HF)" .
hvdc:CONTRACTOFCO_PORT_CHARGE_HF a hvdc:CostCenter ; rdfs:label "CONTRACT(OFCO PORT CHARGE HF)" .
hvdc:PORT_HANDLING_CHARGE a hvdc:CostCenter ; rdfs:label "PORT HANDLING CHARGE" .
hvdc:PORT_HANDLING_CHARGEBULK_CARGO_EQUIPMENT a hvdc:CostCenter ; rdfs:label "PORT HANDLING CHARGE(BULK CARGO_EQUIPMENT)" .
hvdc:PORT_HANDLING_CHARGEBULK_CARGO_MANPOWER a hvdc:CostCenter ; rdfs:label "PORT HANDLING CHARGE(BULK CARGO_MANPOWER)" .
hvdc:PORT_HANDLING_CHARGECHANNEL_TRANSIT_CHARGES a hvdc:CostCenter ; rdfs:label "PORT HANDLING CHARGE(CHANNEL TRANSIT CHARGES)" .
hvdc:PORT_HANDLING_CHARGEPORT_DUES_and_SERVICES_CHARGES a hvdc:CostCenter ; rdfs:label "PORT HANDLING CHARGE(PORT DUES & SERVICES CHARGES)" .
hvdc:PORT_HANDLING_CHARGEYARD_STORAGE a hvdc:CostCenter ; rdfs:label "PORT HANDLING CHARGE(YARD STORAGE)" .

hvdc:Rule1 a hvdc:MappingRule ;
    hvdc:priority 1 ;
    hvdc:regexPattern "(?i)\\b(Berthing|Pilot\\s*Arrangement|Channel\\s*Transit\\s*Permission)\\b" ;
    hvdc:mapsToCostCenterA hvdc:CONTRACTAF_FOR_BA ;
    hvdc:mapsToCostCenterB hvdc:CONTRACT .

hvdc:Rule2 a hvdc:MappingRule ;
    hvdc:priority 2 ;
    hvdc:regexPattern "(?i)\\b(Cargo\\s*Clearance|Cargo\\s*Clearnace)\\b" ;
    hvdc:mapsToCostCenterA hvdc:CONTRACTAF_FOR_CC ;
    hvdc:mapsToCostCenterB hvdc:CONTRACT .

hvdc:Rule3 a hvdc:MappingRule ;
    hvdc:priority 3 ;
    hvdc:regexPattern "(?i)\\b(Arranging\\s*FW\\s*Supply|FW\\s*Supply|Fresh\\s*Water\\s*Supply)\\b" ;
    hvdc:mapsToCostCenterA hvdc:CONTRACTAF_FOR_FW_SA ;
    hvdc:mapsToCostCenterB hvdc:CONTRACT .

hvdc:Rule4 a hvdc:MappingRule ;
    hvdc:priority 4 ;
    hvdc:regexPattern "(?i)\\b(PTW|Permit\\s*to\\s*Work)\\b" ;
    hvdc:mapsToCostCenterA hvdc:CONTRACTAF_FOR_PTW_ARRG ;
    hvdc:mapsToCostCenterB hvdc:CONTRACT .

hvdc:Rule5 a hvdc:MappingRule ;
    hvdc:priority 5 ;
    hvdc:regexPattern "(?i)\\bOFCO\\s*10%\\s*Handling\\s*Fee\\b" ;
    hvdc:mapsToCostCenterA hvdc:CONTRACTOFCO_HF ;
    hvdc:mapsToCostCenterB hvdc:CONTRACT .

hvdc:Rule6 a hvdc:MappingRule ;
    hvdc:priority 6 ;
    hvdc:regexPattern "(?i)\\bOFCO\\s*Forklift\\s*Handling\\s*Fee\\b" ;
    hvdc:mapsToCostCenterA hvdc:CONTRACTOFCO_FOLK_LIFT_HF ;
    hvdc:mapsToCostCenterB hvdc:CONTRACT .

hvdc:Rule7 a hvdc:MappingRule ;
    hvdc:priority 7 ;
    hvdc:regexPattern "(?i)\\bOFCO\\s*Port\\s*Charge\\s*Handling\\s*Fee\\b" ;
    hvdc:mapsToCostCenterA hvdc:CONTRACTOFCO_PORT_CHARGE_HF ;
    hvdc:mapsToCostCenterB hvdc:CONTRACT .

hvdc:Rule8 a hvdc:MappingRule ;
    hvdc:priority 8 ;
    hvdc:regexPattern "(?i)\\bSAFEEN\\b" ;
    hvdc:mapsToCostCenterA hvdc:PORT_HANDLING_CHARGECHANNEL_TRANSIT_CHARGES ;
    hvdc:mapsToCostCenterB hvdc:PORT_HANDLING_CHARGE .

hvdc:Rule9 a hvdc:MappingRule ;
    hvdc:priority 9 ;
    hvdc:regexPattern "(?i)\\b(ADP|PHC|Port\\s*Dues|Port\\s*Services)\\b" ;
    hvdc:mapsToCostCenterA hvdc:PORT_HANDLING_CHARGEPORT_DUES_and_SERVICES_CHARGES ;
    hvdc:mapsToCostCenterB hvdc:PORT_HANDLING_CHARGE .

hvdc:Rule10 a hvdc:MappingRule ;
    hvdc:priority 10 ;
    hvdc:regexPattern "(?i)\\b(Manpower\\s*Charges|Supervisor|Foreman|Banksman|Riggers|Labour)\\b" ;
    hvdc:mapsToCostCenterA hvdc:PORT_HANDLING_CHARGEBULK_CARGO_MANPOWER ;
    hvdc:mapsToCostCenterB hvdc:PORT_HANDLING_CHARGE .

hvdc:Rule11 a hvdc:MappingRule ;
    hvdc:priority 11 ;
    hvdc:regexPattern "(?i)\\b(Crane|Spreader\\s*Beam|Forklift\\s*charges|Equipment\\s*Charges|Third\\s*Party\\s*Equipment)\\b" ;
    hvdc:mapsToCostCenterA hvdc:PORT_HANDLING_CHARGEBULK_CARGO_EQUIPMENT ;
    hvdc:mapsToCostCenterB hvdc:PORT_HANDLING_CHARGE .

hvdc:Rule12 a hvdc:MappingRule ;
    hvdc:priority 12 ;
    hvdc:regexPattern "(?i)\\b(MGO|Fuel\\s*Supply|Diesel|\\+10\\s*%\\s*as\\s*per\\s*DN)\\b" ;
    hvdc:mapsToCostCenterA hvdc:AT_COSTFUEL_SUPPLY_10000GL ;
    hvdc:mapsToCostCenterB hvdc:AT_COST .

hvdc:Rule13 a hvdc:MappingRule ;
    hvdc:priority 13 ;
    hvdc:regexPattern "(?i)\\b(5000\\s*IG\\s*FW|Water\\s*Supply)\\b" ;
    hvdc:mapsToCostCenterA hvdc:AT_COSTWATER_SUPPLY ;
    hvdc:mapsToCostCenterB hvdc:AT_COST .

hvdc:Rule14 a hvdc:MappingRule ;
    hvdc:priority 14 ;
    hvdc:regexPattern "(?i)\\bForklift\\s*charges\\b" ;
    hvdc:mapsToCostCenterA hvdc:AT_COSTFOLKLIFT ;
    hvdc:mapsToCostCenterB hvdc:AT_COST .

hvdc:Rule15 a hvdc:MappingRule ;
    hvdc:priority 15 ;
    hvdc:regexPattern "(?i)\\b(Mobilization|Demobilization|Consumables|Misc\\.)\\b" ;
    hvdc:mapsToCostCenterA hvdc:AT_COSTCONSUMABLES ;
    hvdc:mapsToCostCenterB hvdc:AT_COST .

hvdc:Rule16 a hvdc:MappingRule ;
    hvdc:priority 16 ;
    hvdc:regexPattern "(?i)\\bEquipment\\s*Pass\\s*Arrangement\\b" ;
    hvdc:mapsToCostCenterA hvdc:CONTRACTAF_FOR_EQUIP_PASS_ARRG ;
    hvdc:mapsToCostCenterB hvdc:CONTRACT .

hvdc:Rule17 a hvdc:MappingRule ;
    hvdc:priority 17 ;
    hvdc:regexPattern "(?i)\\b(Pass\\s*Arrangement|Gate\\s*Pass\\s*Arrangement)\\b" ;
    hvdc:mapsToCostCenterA hvdc:CONTRACTAF_FOR_PASS_ARRG ;
    hvdc:mapsToCostCenterB hvdc:CONTRACT .

hvdc:Rule18 a hvdc:MappingRule ;
    hvdc:priority 18 ;
    hvdc:regexPattern "(?i)\\b(Yard\\s*Storage|Monthly\\s*Rental|Storage)\\b" ;
    hvdc:mapsToCostCenterA hvdc:PORT_HANDLING_CHARGEYARD_STORAGE ;
    hvdc:mapsToCostCenterB hvdc:PORT_HANDLING_CHARGE .

```
