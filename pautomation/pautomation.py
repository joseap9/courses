indexOf(outputs('Concat Body Text'), 'Assessment Status:')

trim(first(split(substring(outputs('Concat Body Text'), add(outputs('Find Assessment Status'), length('Assessment Status:')), 100), ' ')))
