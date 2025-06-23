# diagram.py
from diagrams import Cluster, Diagram, Edge
from diagrams.aws.storage import S3
from diagrams.sap.other import PlaceholderNewServices_Circled
from diagrams.sap.integration import IntegrationSuite_Circled
from diagrams.sap.database_datamanagement import SAPHANACloud_Circled
from diagrams.sap.database_datamanagement import ObjectStore_Circled

# SAP BTP Solution Diagrams and Icons guidelines colours
L0_BLUE_COLOUR = "#0070F2"
L0_FILLED_COLOUR = "#EBF8FF"
L1_BLUE_COLOUR = "#0040B0"
L1_FILLED_COLOUR = "#EBF8FF"
L1_BLUE_COLOUR = "#002A86"
SUCCESS_GREEN_COLOUR = "#188918"
SUCCESS_FILLED_COLOUR = "#F5FAE5"

FIX_GREY_COLOUR = "#7F7F7F"
NON_SAP_AREA_COLOUR = "#595959"

with Diagram("SAP Tech Byte - Exploring the SAP Audit Log service - Guidelines Colours", show=False):
    with Cluster("SAP Business Technology Platform", graph_attr= {"bgcolor": L0_FILLED_COLOUR, "pencolor": L0_BLUE_COLOUR}):
        with Cluster("Subaccount", graph_attr= {"bgcolor": "white", "pencolor": L1_BLUE_COLOUR}):
            cloud_integration = IntegrationSuite_Circled("Cloud Integration")
            object_store = ObjectStore_Circled("Object Store")

            PlaceholderNewServices_Circled("Audit Log service") << Edge(label="Retrieves entries", color=FIX_GREY_COLOUR) << \
            cloud_integration >> Edge(color=FIX_GREY_COLOUR) >> SAPHANACloud_Circled("HANA Cloud")
            cloud_integration >> Edge(color=FIX_GREY_COLOUR) >> object_store
        
    with Cluster("AWS", graph_attr= {"bgcolor": "white", "pencolor": NON_SAP_AREA_COLOUR}):
        object_store >> Edge(label="uses", color=FIX_GREY_COLOUR, style="dotted") >> S3("S3 Bucket")