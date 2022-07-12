from diagrams import Diagram

from diagrams.aws.iot import Iot1Click, IotBoard
from diagrams.aws.iot import IotAction
from diagrams.aws.iot import InternetOfThings
from diagrams.aws.iot import IotActuator
from diagrams.aws.iot import IotAlexaEcho
from diagrams.aws.iot import IotAlexaEnabledDevice
from diagrams.aws.iot import IotAlexaSkill
from diagrams.aws.iot import IotAlexaVoiceService
from diagrams.aws.iot import IotAnalyticsChannel
from diagrams.aws.iot import IotAnalyticsDataSet
from diagrams.aws.iot import IotAnalyticsDataStore
from diagrams.aws.iot import IotAnalyticsNotebook
from diagrams.aws.iot import IotAnalyticsPipeline
from diagrams.aws.iot import IotAnalytics
from diagrams.aws.iot import IotBank
from diagrams.aws.iot import IotBicycle
from diagrams.aws.iot import IotButton
from diagrams.aws.iot import IotCamera
from diagrams.aws.iot import IotCar
from diagrams.aws.iot import IotCart
from diagrams.aws.iot import IotCertificate
from diagrams.aws.iot import IotCoffeePot
from diagrams.aws.iot import IotCore
from diagrams.aws.iot import IotDesiredState
from diagrams.aws.iot import IotDeviceDefender
from diagrams.aws.iot import IotDeviceGateway
from diagrams.aws.iot import IotDeviceManagement
from diagrams.aws.iot import IotDoorLock
from diagrams.aws.iot import IotEvents
from diagrams.aws.iot import IotFactory
from diagrams.aws.iot import IotFireTvStick
from diagrams.aws.iot import IotFireTv
from diagrams.aws.iot import IotGeneric
from diagrams.aws.iot import IotGreengrassConnector
from diagrams.aws.iot import IotGreengrass
from diagrams.aws.iot import IotHardwareBoard
from diagrams.aws.iot import IotHouse
from diagrams.aws.iot import IotHttp
from diagrams.aws.iot import IotHttp2
from diagrams.aws.iot import IotJobs
from diagrams.aws.iot import IotLambda
from diagrams.aws.iot import IotLightbulb
from diagrams.aws.iot import IotMedicalEmergency
from diagrams.aws.iot import IotMqtt
from diagrams.aws.iot import IotOverTheAirUpdate
from diagrams.aws.iot import IotPolicyEmergency
from diagrams.aws.iot import IotPolicy
from diagrams.aws.iot import IotReportedState
from diagrams.aws.iot import IotRule
from diagrams.aws.iot import IotSensor
from diagrams.aws.iot import IotServo
from diagrams.aws.iot import IotShadow
from diagrams.aws.iot import IotSimulator
from diagrams.aws.iot import IotSitewise
from diagrams.aws.iot import IotThermostat
from diagrams.aws.iot import IotThingsGraph
from diagrams.aws.iot import IotTopic
from diagrams.aws.iot import IotTravel
from diagrams.aws.iot import IotUtility
from diagrams.aws.iot import IotWindfarm

with Diagram("diagrams-aws-iot-list", show=False):
    InternetOfThings("InternetOfThings")

    # Iot?...
    Iot1Click("Iot1Click")

    # IotA...
    IotActuator("IotActuator")
    IotAction("IotAction")
    IotAlexaEcho("IotAlexaEcho")
    IotAlexaEnabledDevice("IotAlexaEnabledDevice")
    IotAlexaSkill("IotAlexaSkill")
    IotAlexaVoiceService("IotAlexaVoiceService")
    IotAnalytics("IotAnalytics")
    IotAnalyticsChannel("IotAnalyticsChannel")
    IotAnalyticsDataSet("IotAnalyticsDataSet")
    IotAnalyticsDataStore("IotAnalyticsDataStore")
    IotAnalyticsNotebook("IotAnalyticsNotebook")
    IotAnalyticsPipeline("IotAnalyticsPipeline")
    
    # IotB...
    IotBank("IotBank")
    IotBicycle("IotBicycle")
    IotButton("IotButton")
    IotBoard("IotBoard")

    # IotC...
    IotCar("IotCar")
    IotCart("IotCart")
    IotCamera("IotCamera")
    IotCertificate("IotCertificate")
    IotCoffeePot("IotCoffeePot")
    IotCore("IotCore")

    # IotD...
    IotDesiredState("IotDesiredState")
    IotDeviceDefender("IotDeviceDefender")
    IotDeviceGateway("IotDeviceGateway")
    IotDeviceManagement("IotDeviceManagement")
    IotDoorLock("IotDoorLock")

    # IotE...
    IotEvents("IotEvents")

    # IotF...
    IotFactory("IotFactory")
    IotFireTv("IotFireTv")
    IotFireTvStick("IotFireTvStick")

    # IotG...
    IotGeneric("IotGeneric")
    IotGreengrass("IotGreengrass")
    IotGreengrassConnector("IotGreengrassConnector")

    # IotH...
    IotHardwareBoard("IotHardwareBoard")
    IotHouse("IotHouse")
    IotHttp("IotHttp")
    IotHttp2("IotHttp2")

    # IotJ...
    IotJobs("IotJobs")

    # IotL...
    IotLambda("IotLambda")
    IotLightbulb("IotLightbulb")

    # IotM...
    IotMedicalEmergency("IotMedicalEmergency")
    IotMqtt("IotMqtt")

    # Iot...
    IotOverTheAirUpdate("IotOverTheAirUpdate")

    # IotP...
    IotPolicy("IotPolicy")
    IotPolicyEmergency("IotPolicyEmergency")

    # IotR...
    IotReportedState("IotReportedState")
    IotRule("IotRule")

    # IotS...
    IotSensor("IotSensor")
    IotServo("IotServo")
    IotShadow("IotShadow")
    IotSimulator("IotSimulator")
    IotSitewise("IotSitewise")

    # IotT...
    IotThermostat("IotThermostat")
    IotThingsGraph("IotThingsGraph")
    IotTopic("IotTopic")
    IotTravel("IotTravel")

    # IotU...
    IotUtility("IotUtility")

    # IotW...
    IotWindfarm("IotWindfarm")