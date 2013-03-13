from flask import Flask
app = Flask(__name__)

demand_dict={}#global variable to save the past inputs
IDV_dict={}

weather_crawled_file_name='./weatherdata.csv'
weather_crawled_file=open(weather_crawled_file_name,'r')
weather_crawled_dict=eval(weather_crawled_file.readline())#global variable to save the crawled weather info

    
@app.route('/input', methods = ['POST'])
def api_message():
    from flask import request
    if request.headers['Content-Type'] == 'text/plain':
        return "Text Message: " + request.data

    elif request.headers['Content-Type'] == 'application/data':
        prediction_timeline_file_name='./Predictiontimestamps.csv'
        prediction_outputfile_name = './Prediction_Output.csv'
        print 'Generating Variables from input data ..'
        idv_file_name,Output_header=create_idvs(request.data)
        print 'Variable generation from input data complete..'
        print 'Training SVM ..'
        model=svm_training(idv_file_name,';')
        print 'SVM Training complete...'
        print 'Updating predictions ...'
        update_predictions(model,prediction_timeline_file_name,prediction_outputfile_name,Output_header)
        weather_crawled_file_write=open(weather_crawled_file_name,'w')
        weather_crawled_file_write.write(str(weather_crawled_dict))
        return '\nPredictions updated ...\n'
    else:
        return "415 Unsupported Media Type ;)"

def hello(string):
    return string

def flag_variables(flag_variable_names,IDV_dict,demand_dict):
    flag_dict={}
    for variable_name in flag_variable_names:
        flag_dict[variable_name]=list(set([IDV_dict[key+'_'+variable_name] for key in demand_dict.keys()]))
    return flag_dict

def svm_training(Training_filename,delimiter):
    from sklearn import svm
    Training_file=open(Training_filename,'r')
    header = Training_file.readline()
    y=[]
    x=[]
    for line in Training_file:
        line_split=line.split(delimiter)
        y.append(int(line_split[0]))
        x.append([float(ele) for ele in line_split[1:]])
    clf = svm.SVR(kernel='rbf', C=1e2, gamma=0.0)
    clf.fit(x, y) 
    return clf


def update_predictions(model,prediction_timeline_file_name,prediction_outputfile_name,Output_header):
    import datetime,re,json
    
    prediction_timeline_file=open(prediction_timeline_file_name,'r')
    prediction_outputfile=open(prediction_outputfile_name,'w')
    
    for timestamp in prediction_timeline_file:
        idvs=[]
        str_2_datetime= datetime.datetime(*map(int, re.split('[^\d]', timestamp)[:-1])) # Convert string to datetime object
        est_time=str_2_datetime-datetime.timedelta(seconds=5*60*60)

        IDV={}
            
            
        IDV['dayOfWeek']=str_2_datetime.weekday() #Weekday as a decimal number [0(Sunday),6]
        IDV['hour']=str_2_datetime.hour
        idvs.append(IDV['dayOfWeek'])
        idvs.append(IDV['hour'])
        
        weather_json=json.loads(crawl_weather(est_time)) # crawl and get weather info for the day
            
        for observation in weather_json['history']['observations']:
            observation_dict=eval(str(observation))
            for variable in observation_dict.keys():
                IDV[variable]=observation_dict[variable]



        
        for flag_variable in Output_header[3:]:
            flag_value=flag_variable.split('_')[-1]
            flag_raw_variable=flag_variable.split('_')[-2]
            if str(IDV[flag_raw_variable])==str(flag_value):
                idvs.append(1)
            else:
                idvs.append(0)
                
        prediction=model.predict(idvs)
        if prediction[0]<0:
            prediction[0]=0
        prediction_outputfile.write(timestamp.strip()+','+str(prediction[0])+','+'\n')

    return 

def crawl_weather(date_hour):
    import urllib2,time
    year=str(date_hour.year)
    if date_hour.month < 10:
        month='0'+str(date_hour.month)
    else:
        month=str(date_hour.month)
    if date_hour.day < 10:
        day='0'+str(date_hour.day)
    else:
        day=str(date_hour.day)
    try:
        return weather_crawled_dict[year+month+day]
    except:
        api_response = urllib2.urlopen('http://api.wunderground.com/api/bb59cf96c256cb12/history_'+year+month+day+'/q/DC/Washington.json')    
        time.sleep(10)
        weather_crawled_dict[year+month+day]=str(api_response.read()).replace('\n','')   
        return weather_crawled_dict[year+month+day]

def create_idvs(demand_data_json):
    import json,datetime,re
    global demand_dict
    
    demand_data_str_list = eval(demand_data_json)#Parsing the input data
    idv_output_file_name='./uber_idvs.csv'
    
    idv_output_file=open(idv_output_file_name,'w')
    output_delimiter=';'
    
    #Go through the input data (login time stamps) and add it to demand_dict. 
    for login_time_str in demand_data_str_list:
        str_2_datetime= datetime.datetime(*map(int, re.split('[^\d]', login_time_str)[:-1])) # Convert string to datetime object
        
        try: # check if the day-hour entry is present in dictionary if yes increment the count
            if str_2_datetime.hour < 10: #make sure the format is yyyy-mm-dd-hh. add '0' in hour <10
                demand_dict[str(str_2_datetime.date())+'-0'+str(str_2_datetime.hour)]+=1 
                
            else:
                demand_dict[str(str_2_datetime.date())+'-'+str(str_2_datetime.hour)]+=1
        except:#if the day-hour entry is absent add entry.
            if str_2_datetime.hour < 10:
                demand_dict[str(str_2_datetime.date())+'-0'+str(str_2_datetime.hour)]=1
                # add UTC time equivalent to dictionary EST= UTC- 5 hours
                IDV_dict[str(str_2_datetime.date())+'-0'+str(str_2_datetime.hour)+'_esttime']= str_2_datetime-datetime.timedelta(seconds=5*60*60)
            else:
                demand_dict[str(str_2_datetime.date())+'-'+str(str_2_datetime.hour)]=1
                # add UTC time equivalent to dictionary EST= UTC-5 hours
                IDV_dict[str(str_2_datetime.date())+'-'+str(str_2_datetime.hour)+'_esttime']= str_2_datetime-datetime.timedelta(seconds=5*60*60)
    
    
    for key in demand_dict.keys():# for each day-hour in input
        #day for the week.
        key_datetime= datetime.datetime(*map(int,re.split('[-]',key)))
        IDV_dict[key+'_dayOfWeek']=key_datetime.weekday() #Weekday as a decimal number [0(Sunday),6]
        IDV_dict[key+'_hour']=key_datetime.hour
        #Get weather info into the IDV_dict
        est_time=IDV_dict[key+'_esttime']#get time in EST as this is the time used by the weather api
        weather_json=json.loads(crawl_weather(est_time)) # crawl and get weather info for the day
        
        for observation in weather_json['history']['observations']:
            observation_dict=eval(str(observation))
            #Extract the UTC date and use it as the key.
            year=observation_dict['utcdate']['year']
            month=observation_dict['utcdate']['mon']
            day=observation_dict['utcdate']['mday']
            hour=observation_dict['utcdate']['hour']
            obs_key=year+'-'+month+'-'+day+'-'+hour
            for variable in observation_dict.keys():
                IDV_dict[obs_key+'_'+str(variable)]=observation_dict[variable]

         
       
    #Generate the header for the output file
    Output_header=['number_of_logins']
    
    #Create flag variables
    flag_variable_names=['dayOfWeek','hour','conds','fog','rain','snow','hail','thunder','tornado']
    flag_dict=flag_variables(flag_variable_names,IDV_dict,demand_dict)#get the distinct values taken by each flag variable
    
    #Add flag variables to the Output header
    flag_variable_list=[]
    for variable in flag_variable_names:
        for value in flag_dict[variable]:
            flag_variable_list.append('Flag_'+variable+'_'+str(value))
    Output_header.extend(flag_variable_list)
    
    
    #Write the header to the output file.
    flag=True
    for ele in Output_header:
        if flag:
            idv_output_file.write(str(ele))
            flag=False
        else:
            idv_output_file.write(output_delimiter+str(ele))
    idv_output_file.write('\n')
    
    for timeslot in demand_dict.keys():
        idv_output_file.write(str(demand_dict[timeslot]))
        for flag_variable in flag_variable_list:
            flag_value=flag_variable.split('_')[-1]
            flag_raw_variable=flag_variable.split('_')[-2]
            if str(IDV_dict[timeslot+'_'+flag_raw_variable])==str(flag_value):
                idv_output_file.write(output_delimiter+'1')
            else:
                idv_output_file.write(output_delimiter+'0')
            
        idv_output_file.write('\n')
    return idv_output_file_name,Output_header
        
if __name__ == '__main__':
    app.debug = True
    data=app.run()
