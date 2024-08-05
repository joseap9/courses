indexOf(outputs('Concat Body Text'), 'Assessment Status:')

trim(first(split(substring(outputs('Concat Body Text'), add(outputs('Find Assessment Status'), length('Assessment Status:')), 100), ' ')))

if(contains(outputs('Extract Assessment Status'), 'New'), 'New', if(contains(outputs('Extract Assessment Status'), 'Pending Information/Remediation'), 'Pending Information/Remediation', if(contains(outputs('Extract Assessment Status'), 'Complete'), 'Complete', 'Unknown')))
