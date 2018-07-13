from flask import Flask, render_template
from flask_ask import Ask, statement, request, question
import json, datetime

"""JSON structure example
{ "assignment":
    { "Unit 7" : 
        "criteria" : ["p1", "p2", "m1", "d1"],
        "current" : "p1"
        "dueTime" : [INSERT DATE HERE]
        "timeLeft" : [CURRENT TIME] - "dueTime"
    }
}

"""

app = Flask(__name__)
ask = Ask(app, '/')

STATE = ["INTRO", ""]
ASSIGNMENT = {
    "name" : "",
    "dueDate" : "",
    "criteria" : []
}
jsonFile = ""
with open("./assignments.json") as json_file:
    jsonFile = json.load(json_file)


@ask.launch
def launch():
    #return onContinue()
    speech = "Do you give consent for team alexa sanchez to record your voice ?"
    return question(speech).reprompt(speech)


@ask.intent('agreeIntent')
def agree():
    if STATE[0] == "INTRO":
        return onContinue()
    elif STATE[0] == "ASSIGNMENTQUESTION":
        return addAssignment(STATE[1])
    elif STATE[0] == "DATEQUESTION":
        return addDate(STATE[1])


def onContinue():
    speech = "Welcome to the assignment manager how can I help you?"
    return question(speech).reprompt(speech)


@ask.intent('addAssignmentIntent', convert={'unitNumber' : 'unitNumber'})
def addAssignmentIntent(unitNumber):
    for assignment in jsonFile['assignments']:
        if assignment['unit'] == unitNumber:
            return statement("Assignment already exists... Here is all the information i have about it: {}".format(assignment))
    speech = "you want to add unit {}, is that correct?".format(unitNumber)
    STATE[0] = "ASSIGNMENTQUESTION"
    STATE[1] = unitNumber
    return question(speech).reprompt(speech)


def addAssignment(number):
    speech = "When is assignment {} due?".format(number)
    ASSIGNMENT["name"] = number
    return question(speech).reprompt(speech)


@ask.intent('addAssignmentDateIntent', convert={'date' : 'date'})
def addAssignmentDateIntent(date):
    speech = "Your assignment is due on {} is that correct?".format(date)
    STATE[0] = "DATEQUESTION"
    STATE[1] = date
    return question(speech).reprompt(speech)


def addDate(date):
    ASSIGNMENT["dueDate"] = date.isoformat()
    return question("Please add any criteria that is needed for the assignment")


@ask.intent('addCriteriaIntent', convert={'criteria': 'criteria', 'unitNumber' : 'unitNumber'})
def addCriteriaIntent(criteria, unitNumber):
    for assignment in jsonFile['assignments']:
        if assignment['unit'] == unitNumber:
            if assignment['criteria'] == None:
                assignment['criteria'] = []
            else:
                assignment['criteria'].append(criteria)
                tempArr = {"P" : [], "M" : [], "D" : []}
                for i in assignment['criteria']:
                    if i[0] == "P":
                        tempArr["P"].append(i)
                        tempArr["P"].sort()
                    elif i[0] == "M":
                        tempArr["M"].append(i)
                        tempArr["M"].sort()
                    elif i[0] == "D":
                        tempArr["D"].append(i)
                        tempArr["D"].sort()
                assignment = tempArr["P"]
                assignment.extend(tempArr["M"])
                assignment.extend(tempArr["D"])
    uploadUnit(False)
    return question("adding {} to unit {}".format(criteria, unitNumber))

@ask.intent('uploadUnitIntent')
def uploadUnit(doReturn=True):
    jsonFile['assignments'].append({
        "unit": ASSIGNMENT["name"],
        "criteria": ASSIGNMENT["criteria"].sort(reverse=True),
        "dueDate": ASSIGNMENT["dueDate"]
    })
    with open("assignments.json", "w") as outfile:
        json.dump(jsonFile, outfile)
    speech = "all done is there anything else?"
    if doReturn:
        return question(speech).reprompt(speech)

@ask.intent('timeLeftIntent')
def timeLeftIntent(unitNumber):
    for assignment in jsonFile['assignments']:
        if assignment['unit'] == unitNumber:
            days = (datetime.datetime.strptime(assignment['dueDate'], '%Y-%m-%d') - datetime.datetime.now()).days;
            speech = "You have {} days left for unit {}".format(days, unitNumber)
            return question(speech).reprompt(speech)
    speech = "You do not have unit {} saved...".format(unitNumber)
    return question(speech).reprompt(speech)

@ask.intent('whatNextIntent')
def whatNextIntent(unitNumber):
    for assignment in jsonFile['assignments']:
        if assignment['unit'] == unitNumber:
            speech = "next you need to do {}".format(assignment["criteria"][0])
            return question(speech).reprompt(speech)
    speech = "You do not have unit {} saved...".format(unitNumber)
    return question(speech).reprompt(speech)


@ask.intent('markAsDoneIntent')
def markAsDoneIntent(criteria, unitNumber):
    print(criteria, unitNumber)
    for assignment in jsonFile['assignments']:
        if assignment['unit'] == unitNumber:
            try:
                assignment['criteria'].remove(criteria)
                speech = "marked {} as done for unit {}".format(criteria, unitNumber)
                uploadUnit(False)
            except:
                speech = "{} is already marked as done".format(criteria)
            return question(speech).reprompt(speech)

@ask.intent('tellMeAbout')
def tellMeAbout(unitNumber):
    for assignment in jsonFile['assignments']:
        if assignment['unit'] == unitNumber:
            speech = "unit {} is due on {}, and has the criteria {} left...".format(unitNumber, assignment['dueDate'], assignment['criteria'])
            return question(speech).reprompt(speech)
    speech = "unit {} does not exists".format(unitNumber)
    return question(speech).reprompt(speech)


@ask.intent('disagreeIntent')
def disagree():
    if STATE[0] == "INTRO":
        speech = "Sorry but you cannot continue with the application as we need your consent, " \
                 "We hope you will change your mind..."
        return statement(speech)
    elif STATE[0] == "ASSIGNMENTQUESTION":
        speech = "Alright lets try again. What unit would you like to add ?"
    elif STATE[0] == "DATEQUESTION":
        speech = "Ok lets try again. What is your date?"
    return question(speech).reprompt(speech)


@ask.session_ended
@ask.intent('AMAZON.CancelIntent')
@ask.intent('AMAZON.StopIntent')
def session_ended():
    return "{}", 200


if __name__ == '__main__':
    app.run(debug=True)
