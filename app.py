from flask import Flask, render_template, redirect, url_for
from flask.globals import request
from flask_wtf import FlaskForm
from wtforms import SubmitField, PasswordField, Form, StringField
from wtforms.fields.core import SelectField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask_admin import Admin
import pyrankvote
from pyrankvote import Ballot

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///voters.db'
app.config['SECRET_KEY'] = '12345'

db = SQLAlchemy(app)

#table for users/voters registration/login
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    username = db.Column(db.String, nullable= False, unique=True)
    password = db.Column(db.String, nullable= False, unique=True)
   
#table for voter's votes
class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    voter = db.Column(db.Integer, nullable=False)
    first_choice = db.Column(db.String, nullable=False)
    second_choice = db.Column(db.String, nullable=False)
    third_choice = db.Column(db.String, nullable=False)
    forth_choice = db.Column(db.String, nullable=False)


class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    party = db.Column(db.String, nullable=False)


class Election(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    can1 = db.Column(db.String, nullable=False)
    can2 = db.Column(db.String, nullable=False)
    can3 = db.Column(db.String, nullable=False)
    can4 = db.Column(db.String, nullable=False)
    winner = db.Column(db.String, nullable=False)
    close = db.Column(db.Boolean, nullable=False)


#form for register/login page
class UserForm(FlaskForm):
    name = StringField("Name", validators = [DataRequired()])
    username = StringField("Username", validators = [DataRequired()])
    password = PasswordField("Password", validators = [DataRequired()])
    submit = SubmitField("Submit")

#form for voting page
class VoteForm(FlaskForm):
    candidatesInDb = Candidate.query.all()
    if len(candidatesInDb) < 4:
        can1 = "None"
        can2 = "None"
        can3 = "None"
        can4 = "None"
    else:
        can1 = ''+ candidatesInDb[0].name+' (' + candidatesInDb[0].party + ')'
        can2 = ''+ candidatesInDb[1].name+' (' + candidatesInDb[1].party + ')'
        can3 = ''+ candidatesInDb[2].name+' (' + candidatesInDb[2].party + ')'
        can4 = ''+ candidatesInDb[3].name+' (' + candidatesInDb[3].party + ')'
    first_choice =  SelectField('First Choice', choices=[('Candidate Name (Party)'), (can1), (can2), (can3), (can4)])
    second_choice = SelectField('Second Choice', choices=[('Candidate Name (Party)'), (can1), (can2), (can3), (can4)])
    third_choice =  SelectField('Third Choice', choices=[('Candidate Name (Party)'), (can1), (can2), (can3), (can4)])
    forth_choice =  SelectField('Forth Choice', choices=[('Candidate Name (Party)'), (can1), (can2), (can3), (can4)])
    submit = SubmitField("Vote!")

class EndElectionForm(FlaskForm):
    electionName = StringField("Election Name")
    submit = SubmitField("End Election")

class CandidateForm(FlaskForm):
    electionName = StringField("Election Name", validators = [DataRequired()])
    candidate1 = StringField("Candidate 1", validators = [DataRequired()])
    candidate1Party = StringField("Candidate 1 Party", validators = [DataRequired()])
    candidate2 = StringField("Candidate 2", validators = [DataRequired()])
    candidate2Party = StringField("Candidate 2 Party", validators = [DataRequired()])
    candidate3 = StringField("Candidate 3", validators = [DataRequired()])
    candidate3Party = StringField("Candidate 3 Party", validators = [DataRequired()])
    candidate4 = StringField("Candidate 4", validators = [DataRequired()])
    candidate4Party = StringField("Candidate 4 Party", validators = [DataRequired()])
    submit = SubmitField("Save")


@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    name = None
    username = None
    password = None
    form = UserForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username = form.username.data).first()
        #if no user exist when the db is queried for the user, create one
        if user is None:
            user = User(name = form.name.data, username = form.username.data, password = form.password.data)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('vote', username = form.username.data))
        else:
            #flash "this user already exists, please login your account""
            return redirect(url_for('login', username = username))

    return render_template("register.html",
    name = name,
    username = username,
    password = password,
    form = form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    name = None
    username = None
    password = None    
    form = UserForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username = form.username.data).first()
        #if no user exist when the db is queried for the user, create one
        # flash()
        if user is None:
            return redirect(url_for('register'))

        else:
            username = form.username.data
            user = User.query.filter_by(username = username).first()
            if(form.password.data == user.password):
                #Check if user is Admin. If user is Admin redirect to Admin Portal
                if form.username.data == "Admin" and form.password.data == "**Admin**" and form.name.data == "Admin":
                    return redirect(url_for('election', username = username))

                else:   
                    userId = user.id
                    voter = Vote.query.filter_by(voter = userId).first()
                    if userId != 5:
                        if voter is None:
                            return redirect(url_for('vote', username = username))
                        
                        else:
                            return redirect("success")

    return render_template("login.html",
    name = name,
    username = username,
    password = password,
    form = form)

@app.route('/vote', methods=['GET', 'POST'])
def vote():
    usersname = request.args.get('username', None)
    userId = User.query.filter_by(username = usersname).first().id
    errormessage = None
    first_choice = None
    second_choice = None
    third_choice = None
    forth_choice = None
    form = VoteForm()

    if form.validate_on_submit():
        if (form.first_choice.data == 'Candidate Name (Party)') or (form.second_choice.data == 'Candidate Name (Party)') or (form.third_choice.data == 'Candidate Name (Party)')or (form.forth_choice.data == 'Candidate Name (Party)'):
            # Redirect back to page with error message. Please a unique candidate for each one
            errormessage = "Please Select A Candidate for each choice"
            return render_template("vote.html",
                first_choice = first_choice,
                second_choice = second_choice,
                third_choice = third_choice,
                forth_choice = forth_choice,
                errormessage = errormessage,
                form = form)
        
        if (form.first_choice.data == form.second_choice.data) or (form.first_choice.data == form.third_choice.data) or (form.first_choice.data == form.forth_choice.data) or (form.second_choice.data == form.third_choice.data) or (form.second_choice.data == form.forth_choice.data) or (form.third_choice.data == form.forth_choice.data):
            # redirect back to the page with the error message. Cannot pick one candidate twice
            errormessage = "You cannot pick one candidate twice. Please select unique candidates"
            return render_template("vote.html",
                first_choice = first_choice,
                second_choice = second_choice,
                third_choice = third_choice,
                forth_choice = forth_choice,
                errormessage = errormessage,
                form = form)
        else:
            voter = Vote.query.filter_by(voter = userId).first()
            #
            if voter is None:
                vote = Vote(voter = userId,first_choice = form.first_choice.data, second_choice = form.second_choice.data, third_choice = form.third_choice.data, forth_choice = form.forth_choice.data)
                db.session.add(vote)
                db.session.commit()
            return redirect("success")
        
    #find a way to redirect to the success page
    return render_template("vote.html",
    first_choice = first_choice,
    second_choice = second_choice,
    third_choice = third_choice,
    forth_choice = forth_choice,
    errormessage = errormessage,
    form = form)

@app.route('/success')
def success():
    election = Election.query.filter_by(close = 0).first()
    if election == None:
        # No election is open
        return redirect(url_for("result"))
    return render_template("success.html")

@app.route('/clearElection', methods=['POST'])
def clearElection():
    Candidates = Candidate.query.all()
    VotesInDB = Vote.query.all()
    for candidate in Candidates:
        db.session.delete(candidate)
        db.session.commit()
    for vote in VotesInDB:
        db.session.delete(vote)
        db.session.commit()
    return redirect(url_for('election', username="Admin", noname="noname"))


@app.route('/election' , methods=['GET', 'POST'])
def election():
    usersname = request.args.get('username', None)
    noname = request.args.get('noname', None)

    if usersname != "Admin":
        return redirect(url_for("index"))
    #userId = User.query.filter_by(username = usersname).first().id
    form = CandidateForm()
    electionName = ''
    candidate1 = ''
    candidate1Party = ''
    candidate2 = ''
    candidate2Party = ''
    candidate3 = ''
    candidate3Party = ''
    candidate4 = ''
    candidate4Party = ''
    candidateInDb = Candidate.query.all()
    if candidateInDb != []:
        can1 = Candidate.query.filter_by(id = 1).first()
        can2 = Candidate.query.filter_by(id = 2).first()
        can3 = Candidate.query.filter_by(id = 3).first()
        can4 = Candidate.query.filter_by(id = 4).first()
        if can1 != None:
            candidate1 = can1.name
            candidate1Party = can1.party
        if can2 != None:
            candidate2 = can2.name
            candidate2Party = can2.party
        if can3 != None:
            candidate3 = can3.name
            candidate3Party = can3.party
        if can4 != None:
            candidate4 = can4.name
            candidate4Party = can4.party

    elect = Election.query.order_by(desc(Election.id)).first()

    if(elect == None):
        electionName = None
    else:
        electionName = elect.name
    

    if form.validate_on_submit():
        candidates = Candidate.query.all()
        if len(candidates) != 4:
            # There are no Candidates in the Database
            for i in range(1, 5):
                formCandidateName = request.form.get("candidate"+  str(i))
                formCandidateParty = request.form.get("candidate"+  str(i) +"Party")
                if formCandidateName != '' and formCandidateParty != '':
                    print('Not Empty String')
                    newCandidate = Candidate(name = formCandidateName, party = formCandidateParty)
                    db.session.add(newCandidate)
                    db.session.commit()

            newElection = Election(name = form.electionName.data, can1= "can1", can2= "can2", can3= "can3",can4= "can4",winner= "undecided", close=0 )
            db.session.add(newElection)
            db.session.commit()
            return redirect(url_for('election', username="Admin"))

        else:
            for i in range(1, 5):
                formCandidateName = request.form.get("candidate"+  str(i))
                formCandidateParty = request.form.get("candidate"+  str(i) +"Party")
                j = i-1
                if candidates[j].name != formCandidateName:
                    candidates[j].name = formCandidateName
                if candidates[j].party != formCandidateParty:
                    candidates[j].party = formCandidateParty
            db.session.commit()
            return redirect(url_for('election', username="Admin"))

    if noname == "noname":
        electionName = ''

    return render_template("election.html",
    electionName = electionName,
    candidate1 = candidate1,
    candidate2 = candidate2,
    candidate3 = candidate3,
    candidate4 = candidate4,
    candidate1Party = candidate1Party,
    candidate2Party = candidate2Party,
    candidate3Party = candidate3Party,
    candidate4Party = candidate4Party,
    form = form)

@app.route('/allElection', methods=['GET', 'POST'])
def pastElection():
    usersname = request.args.get('username', None)
    if usersname != "Admin":
        return redirect(url_for("index"))
    allElections = Election.query.all()
    return render_template("allElections.html", elections = allElections)

# END ELECTION AND DISPLAY RESULT

@app.route('/endElection', methods=['GET', 'POST'])
def endElection():
    usersname = request.args.get('username', None)
    openElection = Election.query.filter_by(close = 0).first()

    if usersname != "Admin" and openElection == None:
        return redirect(url_for('result'))
    
    if usersname == "Admin" and openElection == None:
        return redirect(url_for("result", username="Admin"))
    
    form = EndElectionForm()
    electionName = openElection.name

    return render_template("endElection.html", 
    electionName = electionName,
    form = form )

@app.route('/result', methods=['GET', 'POST'])
def result():
    #input the pyrankvote algorithm
    #result should be something the admin will calculate
    #from /election import candidate1 and candidate1Party
    usersname = request.args.get('username', None)

    # form = EndElectionForm()
    openElection = Election.query.filter_by(close = 0).first()
    if openElection == None:
        lastElection = Election.query.order_by(desc(Election.id)).first()
        electionName = lastElection.name
    else:
        electionName = openElection.name
        if(usersname != "Admin"):
            return redirect(url_for("success"))
    # closed = ["one"]
    # lines = None
    # winner = None
    # electionName = lastElection.name

    # if lastElection.close == True:
    #     closed = ["two"]       

    # print(closed)
    candidatesInDb = Candidate.query.all()
    votesInDb = Vote.query.all()

    if len(votesInDb) < 1 and usersname == "Admin":
        print(len(votesInDb))
        #Flash that no one has voted yet
        return redirect(url_for('election', username="Admin"))
    else:   
        #closed = "true"
        can1String = ""+ candidatesInDb[0].name +" ("+candidatesInDb[0].party+")"
        can2String = ""+ candidatesInDb[1].name +" ("+candidatesInDb[1].party+")"
        can3String = ""+ candidatesInDb[2].name +" ("+candidatesInDb[2].party+")"
        can4String = ""+ candidatesInDb[3].name +" ("+candidatesInDb[3].party+")"
        candidate1 = pyrankvote.Candidate(can1String)
        candidate2 = pyrankvote.Candidate(can2String)
        candidate3 = pyrankvote.Candidate(can3String)
        candidate4 = pyrankvote.Candidate(can4String)
    
        candidates = [candidate1, candidate2, candidate3, candidate4]

        ballots = [] 

        for i in range(0, len(votesInDb)):
            # getting candidates voted for by each user from the DB
            can1 = pyrankvote.Candidate(votesInDb[i].first_choice)
            can2 = pyrankvote.Candidate(votesInDb[i].second_choice)
            can3 = pyrankvote.Candidate(votesInDb[i].third_choice)
            can4 = pyrankvote.Candidate(votesInDb[i].forth_choice)

            newBallot = Ballot(ranked_candidates=[can1, can2, can3, can4])
            ballots.append(newBallot)
        
        election_result = pyrankvote.instant_runoff_voting(candidates, ballots)
        
        #result = election_result.GetResult()
        allresult = election_result.GetAllResult()
        #lines = result.candidate_results

        resultList = []
        for res in allresult:
            #print("Hey")
            preResList = [res, allresult[res].candidate_results]
            resultList.append(preResList)

        #print(resultList)

        #lines = result.candidate_results
        winner = election_result.GetWinner()
        winnerString = str(winner)

        election = Election.query.filter_by(close = 0).first()
        if election != None:
            print(election)
            election.can1 = can1String
            election.can2 = can2String
            election.can3 = can3String
            election.can4 = can4String
            election.winner = winnerString
            election.close = 1
            db.session.commit()

    # rint(winner)

    return render_template("result.html", 
    array = resultList, 
    winner = winner, 
    electionName = electionName,
    username = usersname)

#make an error page for non type, 404, 500, attribute error
if __name__ == '__main__':
    app.run(debug=True)