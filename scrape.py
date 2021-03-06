import schedule, time, requests, base64, json, ssl, smtplib
from datetime import datetime, date
from bs4 import BeautifulSoup

#user input for a link to scrape
askLink = input('Enter a Link for scraping: ')
askInterval = input('Rerun interval (in minutes): ')
emailPass = input('Enter email password, "\n"Note: this is the password of the email client that is going to send out the link error messagess: ')
emailSendTo = input('Enter the email that will be receiving the bad link notification: ')

header = ''
if "api" in askLink:
    apiUsername = input('Enter API username: ')
    apiPassword = input('Enter API password: ')

    #encode username and password in bytes --> base64 --> back to string with ISO-8859-1 (could have used utf-8, doesn't matter in this case)
    apiCredEncode = bytes(apiUsername+':'+apiPassword, 'utf-8')
    apiCredEncode = base64.b64encode(apiCredEncode).decode('ISO-8859-1')
    #adding the "Basic" header convention
    header = 'Basic ' + apiCredEncode


#initial link calls
try:
    
    result = requests.get(askLink, headers={'Authorization': header})
    print('Link called -> Status Code:' + str(result.status_code))
    result.raise_for_status()

    content = result.content

    if "api" in askLink:
        #decode response content from bytes to string
        content = content.decode('ISO-8859-1')
        content = json.loads(content)
        
        #accessing the grabbed file content key
        content = content['content']
        content = base64.b64decode(content)


    #bs4 grab decoded bytes from src and decode them to an lxml string s(bs4 -- specified this encoding) 
    soup = BeautifulSoup(content, 'lxml')
    #find <a> tags
    tagLinks = soup.find_all("a")

    #request link
    def getLinkStatusCode(link):
        #try to call if valid successfull return the status code
        try:
            result = requests.get(link)
            result.raise_for_status()
            return str(result.status_code)
        #if timeouted
        except requests.exceptions.HTTPError as err:
            return str(err)
        except requests.exceptions.Timeout as err:
            return 'Timeouted' + str(err)
        #if too many redirects
        except requests.exceptions.TooManyRedirects as err:
            return 'Too many redirects' + str(err)
        #other errors
        except requests.exceptions.RequestException as err:
            return str(err)


    #main job declaration
    def job(tagLinks):
        print("\n\n\n ***New Job Started*** \n\n")
        #Variable definition 
        troubled = []
        good = []
        count = 1
        errString = ''

        #Email Template
        message = """\
        Subject: Bad link notification email

\nPlease review the bad links bellow:\n\n\n"""

        #loop through link list
        for link in tagLinks:

            #parse to take out the href attribute
            link = link['href']

            #if status code 200
            if getLinkStatusCode(link).startswith('2'):
                print(str( count) + ')' + link + ' --> OK(' + getLinkStatusCode(link)  + '):' +  ' --> ' + str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) )
                #append to good array
                good.append( str(count) + ')' + link  + ' --> ' + str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) )
                count += 1

            #if status code is true but not 200
            elif getLinkStatusCode(link) == True and getLinkStatusCode(link) != '200':
                print( str(count) + ')' + ' Error ' + getLinkStatusCode(link) + ' -->'  + ' --> ' + str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) )
                #append to troubled array
                troubled.append( str(count) + ')' + link  + ' --> '  + ' --> ' + str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + "\nError" + getLinkStatusCode(link) + "\n" )
                count += 1

            #if status code is not true
            else:
                print( str(count) + ')' + link + ' --> Error ' + getLinkStatusCode(link)  + ' --> ' + str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) )
                #append to troubled array
                troubled.append( str(count) + ')' + link  + ' --> ' + str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + "\nError " + getLinkStatusCode(link) + "\n" )
                count += 1

        #Job Summary
        print("\n\n\n***Job Ended***\n")
        print("\nGood: " + str(len(good))+ "\n")
        for elem in good:
            print(elem)
        print("\nBad:" + str(len(troubled))+ "\n")
        for err in troubled:
            print(err)
            errString += "\t" + err

        #Email Sending Starts HERE

        if len(troubled) != 0:
            email = 'development.python.scraper@gmail.com'

            #SSL port
            port = 465

            sslContx = ssl.create_default_context()

            with smtplib.SMTP_SSL('smtp.gmail.com', port, context=sslContx) as mailServer:
                mailServer.login(email, emailPass)
                mailServer.sendmail(email, emailSendTo, message + errString)
                mailServer.quit()

    job(tagLinks)

    #set at what interval should the job rerun
    schedule.every(int(askInterval)).minutes.do(job, tagLinks)

    while 1:
        schedule.run_pending()
        time.sleep(1)

#Give out error if userlink does not
except requests.exceptions.HTTPError as err:
  print(str(err))
except requests.exceptions.RequestException as err:
  print(str(err))









    



