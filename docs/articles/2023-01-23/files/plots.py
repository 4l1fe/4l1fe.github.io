import matplotlib.pyplot as plt
import numpy as np


def get_color(_rdf):
    return plt.get_cmap('Blues')(np.linspace(0.2, 0.7, _rdf.dimensions['rows']))


def get_explode(_rdf):
    return [0.1 for _ in range(_rdf.dimensions['rows']) ]
    
    
# All the names and values of initial data
context_names = rdf.fill('context_name', constant='None')\
                   .group('context_name')\
                   .rollup({'count': ('context_name', rf.stat.count)})
context_values = rdf.fill('context_value', constant='None')\
                    .group('context_value')\
                    .rollup({'count': ('context_value', rf.stat.count)})
fig, axs = plt.subplots(2,1)
axs[0].pie(context_names['count'],
           labels=context_names['context_name'],
           colors=get_color(context_names),
           explode=get_explode(context_names))
axs[0].set_title('Context names') 
axs[1].pie(context_values['count'],
           labels=context_values['context_value'],
           colors=get_color(context_values),
           explode=get_explode(context_values))
axs[1].set_title('Context values')
plt.savefig('data-before.png')

# All the names and values of updated data
context_names = updated_rdf.group('context_name')\
                           .rollup({'count': ('context_name', rf.stat.count)})
context_values = updated_rdf.group('context_value')\
                            .rollup({'count': ('context_value', rf.stat.count)})
fig, axs = plt.subplots(2,1)
axs[0].pie(context_names['count'],
           labels=context_names['context_name'],
           colors=get_color(context_names),
           explode=get_explode(context_names))
axs[1].pie(context_values['count'],
           labels=context_values['context_value'],
           colors=get_color(context_values),
           explode=get_explode(context_values))
plt.savefig('data-after.png')
