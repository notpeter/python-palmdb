READ='READ'
WRITE='WRITE'

DesktopApplications={
	'PALMDB_XML':'PalmDB Default XML Format',
	'PDESK_XML':'PDesk XML',
	'GANTPROJECT':'Gantt Project',
	'TREELINE':'Treeline',
	}

def getDesktopApplicationNameFromID(applicationID):
	return PalmApplications.get(applicationID,'Unknown Application')

