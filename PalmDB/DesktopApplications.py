READ='READ'
WRITE='WRITE'

DesktopApplications={
	'PALMDB_XML':'PalmDB Default XML Format',
	'PALMDB_XML_TODOLIST':'PalmDB Default Palm ToDo List Format',
	'PDESK_XML':'PDesk XML',
	'PDESK_PROJECT_LIST_XML':'PDesk Project List XML',
	'GANTPROJECT':'Gantt Project',
	'TREELINE':'Treeline',
	}

def getDesktopApplicationNameFromID(applicationID):
	return DesktopApplications.get(applicationID,'Unknown Application')

