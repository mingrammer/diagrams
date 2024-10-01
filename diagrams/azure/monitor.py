from . import _Azure

class _Monitor(_Azure):
    _type = "monitor"
    _icon_dir = "resources/azure/monitor"
    

class Monitor(_Monitor):
    _icon = "monitor.png"

class Metrics(_Monitor):
    _icon = "metrics.png"
    
class LogsAnalytics(_Monitor):
    _icon = "logs.png"
    
class ChangeAnalysis(_Monitor):
    _icon = "change-analysis.png"