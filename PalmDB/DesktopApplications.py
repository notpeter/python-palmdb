READ = 'READ'
WRITE = 'WRITE'

DesktopApplications = {
    'PALMDB_XML': 'PalmDB Default XML Format',
    'PALMDB_XML_TODOLIST': 'PalmDB XML TODO List format',
    'PDESK_XML': 'PDesk XML',
    'PDESK_PROJECT_LIST_XML': 'PDesk Project List XML',
    'GANTPROJECT': 'Gantt Project',
    'TREELINE': 'Treeline',
}


def getDesktopApplicationNameFromID(applicationID):
    return DesktopApplications.get(applicationID, 'Unknown Application')


def getDesktopApplicationDict():
    return DesktopApplications
