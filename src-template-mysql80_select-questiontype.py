import mysql.connector
import sys
import json

class Resultat:
    puntuacio = 0.0
    missatges = []

    def __init__(self):
        self.puntuacio = 10
        self.missatges = [['Test', 'Comment', 'IsCorrect']]


cnx = mysql.connector.connect(host="{{ QUESTION.parameters.mysqlhost | e('py') }}"
                                ,user="{{ QUESTION.parameters.mysqluser | e('py') }}"
                                ,password="{{ QUESTION.parameters.mysqlpwd | e('py') }}"
                                ,database="{{ QUESTION.parameters.mysqldb | e('py') }}"
                                ,auth_plugin="mysql_native_password")



stmStudent = """{{ STUDENT_ANSWER | e('py') }}"""
stmSolucio = """{{ QUESTION.answer | e('py') }}"""

stmStudentOK = False
retorn = Resultat()
try:
    curStm = cnx.cursor(buffered=True)
    curStm.execute("SET SESSION max_execution_time=1000;")
    curStm.execute(stmStudent)
    
    stmStudentOK = True
    retorn.puntuacio = 0.0
except mysql.connector.Error as e:
    #La sentència dona error d'execució
    retorn.puntuacio = 0.0
    retorn.missatges.append(["CHECK_STATMENT", "Sentència errònia: {}".format(e),  False])



if stmStudentOK :
    showChecks = {{ QUESTION.parameters.show_checks ? 1 : 0 }}
    retorn.missatges = [['Test', 'Comment','Got','Expected', 'IsCorrect']]
    numOk = 0 # variable que contindrà el numero de Checks que han donat OK
    numChecks = {{ QUESTION.parameters.checks|length }}
    curStmSolucio = cnx.cursor(buffered=True)
    curStmSolucio.execute(stmSolucio)
    # Comprovem el número de registres
    if {{ "CHECK_NUM_ROWS" in QUESTION.parameters.checks ? 1 : 0 }}:
        mark = False
        if curStm.rowcount == curStmSolucio.rowcount:
            mark = True
            numOk += 1
        if showChecks:
            retorn.missatges.append(["CHECK_NUM_ROWS", "Num. files " + ("correcte" if mark else "incorrecte"),curStm.rowcount, curStmSolucio.rowcount, mark])

    # Comprovem el número de camps
    if {{ "CHECK_NUM_FIELDS" in QUESTION.parameters.checks ? 1 : 0 }}:
        mark = False
        if len(curStm.column_names) == len(curStmSolucio.column_names):
            mark = True
            numOk += 1
        if showChecks:
            retorn.missatges.append(["CHECK_NUM_FIELDS", "Num. camps " + ("correcte" if mark else "incorrecte"),len(curStm.column_names),len(curStmSolucio.column_names),  mark])
    
    # Comprovem el nom dels camps
    if {{ "CHECK_NAME_FIELDS" in QUESTION.parameters.checks ? 1 : 0 }}:
        mark = False    
        campsUsuari = curStm.column_names
        campsUsuari = [x.upper() for x in campsUsuari]
        campsSolucio = curStmSolucio.column_names
        campsSolucio= [x.upper() for x in campsSolucio]
        dif = [item for item in campsUsuari if item not in campsSolucio]
        if len(dif)==0:
            mark = True
            numOk += 1
        if showChecks:
            retorn.missatges.append(["CHECK_NAME_FIELDS", "Noms de camps " + ("correcte" if mark else "incorrecte"),",".join(curStm.column_names),",".join(curStmSolucio.column_names),  mark])    

    # Comprovem l'ordre del nom dels camps
    if {{ "CHECK_ORDER_NAME_FIELDS" in QUESTION.parameters.checks ? 1 : 0 }}:
        mark = True
        numChecks -= 1
        if showChecks:
            retorn.missatges.append(["CHECK_ORDER_NAME_FIELDS", "No comprovat","-","-",  mark])    
        
    # Comprovem l'eficiència    
    if {{ "CHECK_EFFICIENCY" in QUESTION.parameters.checks ? 1 : 0 }}:
        mark = True
        numChecks -= 1
        if showChecks:
            retorn.missatges.append(["CHECK_EFFICIENCY", "No comprovat","-","-",  mark])    

#Com que CHECK_ORDER_NAME_FIELDS I CHECK_EFFICIENCY no estan programats
#traurem la seva ponderació fent un numChecks -= 1 en cada cas.

    # Comprovem els registres
    #uniformaitzarOrderBy(stm,stmSolucio)
    mark = False
    if curStm.rowcount == curStmSolucio.rowcount:
        i = 0
        diffTrobada = False
        debug_rows = "Debug: "
        try:
            while i<curStmSolucio.rowcount and not diffTrobada:
            #for i in range(0,curStmSolucio.rowcount):
                #Hauriem de comprovar columna per columna.
                for c in range(0,len(curStmSolucio.column_names)):
                    diffTrobada = curStmSolucio._rows[i][c] != curStm._rows[i][c]
                    tsolucio = curStmSolucio._rows[i][c]
                    talumne = curStm._rows[i][c]
                    #debug_rows += debugfiles + "<br/>row (" + str(i) + ") " + str(tsolucio) + "==" + str(talumne)
                i += 1
        except IndexError:
            diffTrobada = True
    
        if not diffTrobada:
            mark = True
            
    checkResultsOK = mark
    if showChecks:
        retorn.missatges.append(["CHECK_RESULTS", "Resultat " + ("correcte" if mark else "incorrecte"),"-","-",  mark])    

    
    scoreChecks = numOk * ( {{QUESTION.parameters.percent_checks}}/numChecks )
    retorn.puntuacio = ((1.0-{{QUESTION.parameters.percent_checks}}) if checkResultsOK else 0) + scoreChecks 

    if not showChecks:
        if retorn.puntuacio == 1.0:
            retorn.missatges.append(["CHECK_RESULTS", "Resultat correcte","-","-",  1])    
        else :    
            retorn.missatges.append(["CHECK_RESULTS", "Redsultat incorrecte","-","-",  0])    

prologuehtml = "<h2>Prologue</h2>"
prologuehtml = ""
html = """Wasn't that <b>FUN</b>
And here's an image:<br>
<br>Followed by nothing."""
html += "Puntuació " + str(retorn.puntuacio)
html = ""

# Lastly return the JSON-encoded result required by a combinator grader
print(json.dumps({'prologuehtml': prologuehtml,
                'testresults': retorn.missatges,
                'epiloguehtml': html,
                'fraction': retorn.puntuacio
}))      