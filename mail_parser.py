import re
import json
from datetime import datetime
import pytz

class MailParser:
    '''Class for parsing emails from Circuit Providers'''


    def __init__(self, mail):
        self.provider = '' #provider name
        self.ticket_type='' #type of activity
        self.provider_ref = '' #provider ticket id
        self.start_time = '' #planned start
        self.end_time = '' #planned end
        self.service = '' #service ID (provider ref)
        self.parse(mail) 

    def parse(self, mail):
        """
        Function to parse email from the PW provider and extract following information:
        provider name, provider ticket reference, impacted service, start/end time of work
        """

        providers_patterns = {
            #Dictionary containing all known PW providers and related email-subject patterns
            #Assumption here is that provider name can be extracted from the email subject but in real-life
            #it might needed to be taken from the email header
            
            'Fiber Provider' : r'Subject:.+?from (?P<provider>Fiber Provider)',
            'Some-Other Provider':  r'Subject:.+?(?P<provider>Some-Other Provider)'
        }

        with open(mail,'r') as f:
            txt = f.read()
            for provider, pattern in providers_patterns.items():
                #find provider name based on the email pattern
                if re.match(pattern, txt):
                    self.provider = provider
            #extract ticket parameters from the email using customized function 
            if self.provider == 'Fiber Provider':
                self.fiber_provider_parse(txt)
            elif self.provider == 'Some-Other Provider':
                self.some_other_provider_parse(txt)
            else:
                raise Exception('No provider found')

    
    def fiber_provider_parse(self, txt):
            """
            Custom function to parse emails from Fiber Provider
            """

            #PLANNED WORK (PW) Notification
            p1 = re.compile(r'^PLANNED WORK \(PW\) Notification',re.MULTILINE)

            #PW Reference number: PWIC12345
            p2 = re.compile(r'^PW Reference number:\s(?P<pw_ref>\w+)',re.MULTILINE)
            
            #Start Date and Time: 2019-Apr-09 06:00 UTC
            p3 = re.compile(r'^Start Date and Time:\s(?P<start_time>[\w\-]+\s[0-9:]+)\s(?P<start_tz>[A-Za-z]+)', re.MULTILINE)

            #End Date and Time: 2019-Apr-09 10:00 UTC
            p4 = re.compile(r'^End Date and Time:\s(?P<end_time>[\w\-]+\s[0-9:]+)\s(?P<end_tz>[A-Za-z]+)', re.MULTILINE)
            
            #Service ID: IC-99999
            p5 = re.compile(r'^Service ID:\s(?P<service>[\w\-]+)',re.MULTILINE)



            if p1.search(txt):
                #Notifcation about new planned work
                self.ticket_type = 'New maintenance'
            
                try:
                    self.provider_ref = p2.search(txt).group('pw_ref')

                    timeformat = '%Y-%b-%d %H:%M' #Date/Time format used by Fiber Provider
                    
                    local_start_time = datetime.strptime(p3.search(txt).group('start_time'), timeformat)
                    start_tz = p3.search(txt).group('start_tz')
                    self.start_time = MailParser.convert_time(local_start_time, start_tz)

                    local_end_time = datetime.strptime(p4.search(txt).group('end_time'), timeformat)
                    end_tz = p4.search(txt).group('end_tz')
                    self.end_time = MailParser.convert_time(local_end_time, end_tz)

                    self.service = p5.search(txt).group('service')
                except:
                    raise Exception('Cannot parse some properties')

            #here would go conditions for cancelled work and modification
            # but without actual email its difficult to create
            #  
            return self

    def some_other_provider_parse(self, mail):
        """
        Custom function to parse emails from Some-Other Provider
        """
        #Placeholder
        return self
    
    @staticmethod
    def convert_time(time, tz):
        """
        Function converts given time in local timezone (tz) to UTC and standarized format %Y-%m-%d %H:%M)
        This would require further work as many abbreviations are not directly mapped to timezone in pytz module
        """
        return pytz.timezone(tz).localize(time).astimezone(pytz.UTC).strftime('%Y-%m-%d %H:%M')


    def get_ticket_info(self):
        """ 
        Returns all parameters in JSON format so they can be send to an external application
        """
        return json.dumps(self.__dict__)


if __name__ == "__main__":
    """
    Example of parsing provider_email.txt and displaying info
    Example output:
    {"provider": "Fiber Provider", "ticket_type": "New maintenance", "provider_ref": "PWIC12345", "start_time": 
    "2019-04-09 06:00", "end_time": "2019-04-09 10:00", "service": "IC-99999"}
    """

    ticket = MailParser('C:\\Users\\Lukasz\\Documents\\python\\packetfabric\\provider_email.txt')
    print(ticket.get_ticket_info())
