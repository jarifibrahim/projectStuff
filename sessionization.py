# Sample script to parse web server log
import datetime as dt
import pprint 

# sample log file
infile = open('access_log', 'r')

line = []
sessions = dict()

# calculate session time for each ip
def calc_session_time(times):
    total_time = []
    diff = [[]]
    if len(times) < 2:
        return
    for i,j in zip(times[:-1], times[1:]):
        if j-i > dt.timedelta(minutes=10) and diff[0]:
            diff.append([j-i])
        else:
            diff[-1].append(j-i)
    for di in diff:
        total = dt.timedelta(0)
        for d in di[1:]: 
            total += d
        total_time.append(str((total.seconds//60)%60) + 'm ' + str(total.seconds%60) + 's')
    return total_time
    
for log_line in infile:
    items = []
    part = log_line.split(" ")[:9]
    
    # Skip requests for the following type of files
    if part[6].split('.')[-1] in ['jpg', 'ico', 'cgi', 'gif', 'png', 'js', 'css', 'txt']:
        continue
    
    # Skip files without a "GET" or "POST" type request
    elif part[5]== '"-"':
        continue
        
    items.append(part[0]) # IP address
    date_object = dt.datetime.strptime(part[3][1:], '%d/%b/%Y:%H:%M:%S') # Time stamp
    items.append(date_object)
    items.append(part[6])  # Requested url
    line.append(items)

for l in line:
    key = l[0]
    item = dict()
    if key in sessions.keys():  # IP already exists
        item = sessions[key]
        item['datetime'].append(l[1]) # Add datetime
        item['urls'].append(l[2])       # Add urls
        item['total_session_time'] = calc_session_time(item['datetime'])
    else:   # IP does not exists
        item['datetime'] = [l[1]]
        item['urls'] = [l[2]]
        item['total_session_time'] = '0s'
        sessions[key] = item

with open('data.json', 'w') as fp:
    pprint.pprint(sessions, fp, width=1)
