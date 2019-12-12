import filemapper as fm
import os.path
import wikipedia
import math
from random import randint
from urllib.request import urlopen
import json
import threading
from wikipedia.exceptions import DisambiguationError, PageError

tries = 0
correct = 0

langs = []
percentRatio = []
path = fm.load('constlearnt')
currentdict = {}
alphabet = [chr(i) for i in range(ord('a'),ord('z')+1)]

def testAlgorithm(i, max, isLearning, isWiki):
    arr = ["pl", "en", "fr", "de", "es"]
    lang = arr[randint(0, 4)]
    wikipedia.set_lang(lang)
    url = "https://" + lang + ".wikipedia.org/w/api.php?action=query&list=random&format=json&rnnamespace=0&rnlimit=1"
    response = urlopen(url)
    data = json.loads(response.read())
    title = (((data['query'])['random'])[0])['title' ]
    t1 = threading.Thread(handleTestThread(title, lang, i, max, isLearning, isWiki))
    t1.start()
    t1.join()

def handleTestThread(title, lang, i, max, isLearning, isWiki):
    searchresponse = wikipedia.search(title)
    try:
        page = wikipedia.page(searchresponse[0])
        print("Wylosowany artykul to: " + title + " -  jest w jezyku " + lang)
        if(isLearning):
            learnFromText(page.content, lang)
        calculateDistance(page.content, lang, i, max, isLearning, isWiki)
    except DisambiguationError:
        testAlgorithm(i, max, isLearning, isWiki)
        print("Zly artykul")
    except PageError:
        testAlgorithm(i, max, isLearning, isWiki)
        print("Duplikat referencji")

def getDictFromText(text, isPercent):
    lettercount = 0
    currentdict = {}
    for singleletter in text:
        if (ord(singleletter) >= 97 and ord(singleletter) <= 122) or (ord(singleletter) >= 65 and ord(singleletter) <= 90):
            lettercount = lettercount + 1
            if singleletter.lower() in currentdict:
                currentdict[singleletter.lower()] = currentdict[singleletter.lower()] + 1
            else:
                currentdict[singleletter.lower()] = 1
    if isPercent:
        for keys in currentdict:
            currentdict[keys] = (float(currentdict[keys]) / float(lettercount))*100
    currentdict["letternumber"] = lettercount
    return currentdict

def euclideanDistance(lang1, lang2):
    distance = 0.0
    for i in alphabet:
        po = pow((float(lang1[i]) - float(lang2[i])), 2)
        distance = distance + po
    return math.sqrt(distance)

def calculateDistance(text, lang, i, max, isLearning, isWiki):
    path = fm.load('constlearnt')
    dicts = []
    distances = {}
    for f in path:
        fromFileInfo = {}
        isFirstLine = True
        for y in fm.read(f):
            if isFirstLine:
                isFirstLine = False
            else:
                arr = y.split('/')
                fromFileInfo[arr[0]] = arr[1].replace("\n", "")
        dicts.append(fromFileInfo)
        (dicts[len(dicts)-1])["language"] = f.replace(".txt","").replace("learned_","")
    newtextdict = getDictFromText(text, True)
    for dic in dicts:
        for ch in alphabet:
            if not ch in dic:
               dic[ch] = 0.0
            if not ch in newtextdict:
                newtextdict[ch] = 0.0
        distances[dic["language"]] = euclideanDistance(newtextdict, dic)
    print("Zgaduje, iz artykul jest w jezyku " + min(distances, key=lambda k: distances[k]))
    global tries
    global correct
    tries = tries+1
    if min(distances, key=lambda k: distances[k]) == lang:
        correct = correct+1
        print("Jezyk sie zgadza")
    else:
        print("Jezyk sie nie zgadza")
    print(("Skutecznosc zgadywania to w tym momencie " + str(float(correct)/float(tries)*100) + " proby: " + str(tries) + " poprawne: " + str(correct)))
    print("\n")
    if isWiki:
        testAlgorithm(i, max, isLearning, isWiki)

def handleThread(title, language):
    searchresponse = wikipedia.search(title)
    try:
        page = wikipedia.page(searchresponse[0])
        learnFromText(page.content, language)
        print("Wylosowany artykul to: " + title)
    except DisambiguationError:
        print("Zly artykul")
    except PageError:
        print(("Duplikat artykulow"))

def getRandomArticleFromWikipedia(i, max, language):
    wikipedia.set_lang(language)
    url = "https://" + language  + ".wikipedia.org/w/api.php?action=query&list=random&format=json&rnnamespace=0&rnlimit=1"
    response = urlopen(url)
    data = json.loads(response.read())
    title = (((data['query'])['random'])[0])['title']
    t1 = threading.Thread(handleThread(title, language))
    t1.start()
    t1.join()
    i = i + 1
    if i < max:
        getRandomArticleFromWikipedia(i, max, language)
    else:
        return

def handleFile(i):
    if os.path.isfile("learned_" + i["language"] + ".txt"):
        fromFileInfo = {}
        currentweight = float(i["letternumber"])
        with open("learned_" + i["language"] + ".txt", 'r') as file:
            isFirstLine = True
            for y in file:
                if isFirstLine:
                    wholeweight = y
                    isFirstLine = False
                else:
                    arr = y.split('/')
                    fromFileInfo[arr[0]] = arr[1].replace("\n", "")
        for keys in i:
            if (str(keys) != "letternumber" and str(keys) != "language") and type(i[keys]) is not str:
                if keys in fromFileInfo:
                    fromFileInfo[keys] = float(float(float(fromFileInfo[keys])*float(wholeweight)) + float(float((float(i[keys])/float(currentweight))*100)*float(currentweight))) / (float(float(currentweight)+float(wholeweight)))
                else:
                    fromFileInfo[keys] = float(i[keys]) / ((float(wholeweight) + float(currentweight)))
        file = open("learned_" + i["language"] + ".txt", 'w')
        file.write(str(float(currentweight)+float(wholeweight)) + "\n")
        for keys, values in fromFileInfo.items():
            if keys != "language" and keys != "letternumber":
                file.write(keys + "/" + str(values) + "\n")
        file.close()
    else:
        for ch in alphabet:
            if not ch in i:
                i[ch] = 0
        file = open("learned_" + i["language"] + ".txt", 'w')
        file.write(str(float(i["letternumber"])) + "\n")
        for keys, values in i.items():
            if (str(keys) != "letternumber" and str(keys) != "language"):
                i[keys] = float(float(values / float(i["letternumber"])) * 100)
                file.write(keys + "/" + str(float(float(values / float(i["letternumber"])) * 100)) + "\n")
        file.close()


def learnFromText(text, languagename):
    dict = getDictFromText(text, False)
    dict["language"] = languagename
    handleFile(dict)

def learnFromWikipedia():
    arr = [ "pl" , "en", "fr", "de", "cs"]
    print("Wybierz jezyk, ktorego algorytm ma sie nauczyc ")
    print(arr)
    language = input()
    for i in arr:
        if language == i:
            break
    else:
        print("Wybrano zly jezyk")
        return
    wikipedia.set_lang(language)
    searchquery = input("Podaj nazwe strony, ktora chcesz wyszukac ")
    searchresponse = wikipedia.search(searchquery)
    for i in searchresponse:
        i = i.replace("u'", "")
        print(i)
    pagename = input("Przepisz dokladnie nazwe strony, ktorej chcesz sie nauczyc ")
    for i in searchresponse:
        if pagename == i:
            break
    else:
        print("Wpisano zla nazwe strony")
        return
    newpage = wikipedia.page(pagename)
    print(newpage.content)
    learnFromText(newpage.content, language)

def learnFromFiles():
    path = fm.load('resources')
    for f in path:
        isFirst = True
        lettercount = 0
        for i in fm.read(f):
            if isFirst:
                for x in langs:
                    if i.replace("\n", "") == x.get("language"):
                        currentdict = x
                        break
                else:
                    langs.append({"language": i.replace("\n", "")})
                    currentdict = langs[len(langs)-1]
                isFirst = False
            else:
                for singleletter in i:
                    if (ord(singleletter) >= 97 and ord(singleletter)<=122) or (ord(singleletter) >= 65 and ord(singleletter)<=90):
                        lettercount = lettercount +1
                        if singleletter.lower() in currentdict:
                            currentdict[singleletter.lower()] = currentdict[singleletter.lower()]+1
                        else:
                            currentdict[singleletter.lower()] = 1
        if "letternumber" in currentdict:
            currentdict["letternumber"] = currentdict["letternumber"] +  float(lettercount)
        else:
            currentdict["letternumber"] = float(lettercount)
    for i in langs:
        handleFile(i)

def showMenu():
    print("")
    print("Co chcesz zrobic?")
    print( "1. Ucz sie z plikow w katalogu /resources/")
    print( "2. Ucz sie z wikipedii")
    print( "3. Ucz sie z wprowadzonego w konsole tekstu")
    print( "4. Ucz sie z pomoca losowych artykulow na wikipedii\n")
    print( "5. Przetestuj algorytm bez uczenia - wikipedia")
    print( "6. Przetestuj algorytm z uczeniem - wikipedia")
    print( "7. Przetestuj wpisujac w kosnoli")
    choose = int(input())
    if choose == 1:
        learnFromFiles()
    elif choose == 2:
        learnFromWikipedia()
    elif choose == 3:
        arr = ["pl", "en", "fr", "de", "cs"]
        print(arr)
        languagename = input("Podaj nazwe jezyka z listy powyzej ")
        for i in arr:
            if languagename == i:
                break
        else:
            print("Blad: Wybrano jezyk spoza tablicy")
            showMenu()
        text = input("Podaj swoj tekst ")
        learnFromText(text, languagename)
    elif choose == 4:
        arr = ["pl", "en", "fr", "de", "cs"]
        print(arr)
        languagename = input("Podaj nazwe jezyka z listy powyzej ")
        for i in arr:
            if languagename == i:
                break
        else:
            print("Blad: Wybrano jezyk spoza tablicy")
            showMenu()
        variable = int(input("Podaj liczbe artykulow"))
        getRandomArticleFromWikipedia(0, variable, languagename)
    elif choose==5:
        n = input("Ile razy przetestowac algorytm?")
        testAlgorithm(0, n, False, True)
    elif choose==6:
        n = input("Ile razy przetestowac algorytm?")
        testAlgorithm(0, n, True, True)
    elif choose ==7:
        arr = ["pl", "en", "fr", "de", "cs"]
        print(arr)
        languagename = input("Podaj nazwe jezyka z listy powyzej ")
        for i in arr:
            if languagename == i:
                break
        else:
            print("Blad: Wybrano jezyk spoza tablicy")
            showMenu()
        text = input("wpisz tekst")
        calculateDistance(text, languagename, 1, 0, False, False)
    else:
        print("Nie wybrano poprawnie ")

showMenu()
