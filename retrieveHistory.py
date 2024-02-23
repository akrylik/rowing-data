#!/usr/bin/python3.11
# -*- coding: utf-8 -*-

"""

Scraping tool to download 10 years of workout history as *.fit files. You will be all able to download them in Garmin Connect.

Usage:
    ./retrieveHistory.py myUser myPassword ${HOME}/Downloads

"""


import datetime
import logging
import multiprocessing
import os
import re
import requests
import sys


logging.basicConfig(
    format="%(asctime)s - %(message)s", datefmt="%Y/%m/%d %H:%M:%S", level=logging.INFO
)


CONCEPT2_LOGIN = None
CONCEPT2_PASSWORD = None
OUTPUT_DIR = "."

CONCEPT2_URL = "log.concept2.com"
CONCEPT2_URL_LOG = "https://{0}/login".format(CONCEPT2_URL)

CURRENT_YEAR = datetime.date.today().year
MAX_PERIOD = 10


trainingPattern = "https://{0}/profile/[0-9]+/log/[0-9]+".format(CONCEPT2_URL)
trainingRegex = re.compile(trainingPattern)


def warmup(allArgs):
    """
    Initializes global variables with program arguments.

        Parameters:
            allArgs (list): list of arguments.

        Returns:
            Nothing
    """

    global CONCEPT2_LOGIN
    global CONCEPT2_PASSWORD
    global OUTPUT_DIR

    if (len(allArgs)) != 4:
        print(
            "three arguments are needed, login + password + output_dir, got {0}.".format(
                len(allArgs) - 1
            )
        )
        raise SystemExit(1)

    if len(allArgs[1]) < 4 or len(allArgs[2]) < 4 or len(allArgs[3]) < 4:
        print("One ore more arguments seem to be to short.")
        raise SystemExit(2)

    CONCEPT2_LOGIN = allArgs[1]
    CONCEPT2_PASSWORD = allArgs[2]
    OUTPUT_DIR = allArgs[3]


def getAuthCookie():
    """
    Log to Concept2 Logbook to retrieve an authentication cookie which can will be reuse.

        Parameters:
            Nothing.

        Return:
            authCookie (str): an HTTP cookie with credentials.
    """

    response = requests.post(
        url=CONCEPT2_URL_LOG,
        data={"username": CONCEPT2_LOGIN, "password": CONCEPT2_PASSWORD},
    )
    authCookie = response.headers["Set-Cookie"]
    response.close

    return authCookie


def collectTraining(oneCustomHeaders, oneYear):
    """
    Function designed to get all workouts URLs for one season/year.

        Parameters:
            oneCustomHeaders (dict): HTTP headers with credentials.
            oneYear (int): target season/year.

        Return:
            listWorkouts (list): A list of workout URLs.
    """

    listWorkouts = []

    season = requests.get(
        url="https://{0}/season/{1}".format(CONCEPT2_URL, oneYear),
        headers=oneCustomHeaders,
    )
    htmlSeason = season.text
    season.close

    matchResult = re.findall(trainingRegex, htmlSeason)

    for oneLink in matchResult:
        listWorkouts.append(oneLink)

    return set(listWorkouts)


def getAllWorkouts(oneRangeSeasons, oneCustomHeaders):
    """
    Function designed to retrieve all workouts URLs for a range of seasons/years.

    Parameters:
        oneRangeSeasons (range): range of years from now to past.
        oneCustomHeaders (dict): HTTP headers with credentials.

    Return:
        result (list): A list of workout URLs.
    """

    result = {}

    for oneSeason in oneRangeSeasons:

        logging.info("Looking for {0} season...".format(oneSeason))
        yearTrainings = collectTraining(oneCustomHeaders, oneSeason)

        if len(yearTrainings) > 0:
            result[oneSeason] = yearTrainings

    return result


def downloadWorkout(oneOutputDir, oneYear, oneLink, oneCustomHeaders):
    """
    Function designed to

        Parameters:
            oneOutputDir (str): root directory where download workout file.
            oneYear (int): workout season/year.
            oneLink (str): workout URL.
            oneCustomHeaders (dict): HTTP headers with credentials.

        Return:
            True if OK, then False.

    """

    logging.debug("Downloading {0} workout...".format(oneLink))

    dataFit = requests.get(url=oneLink, headers=oneCustomHeaders)

    if dataFit.status_code != 200:
        return False

    dataFit.close

    workoutId = oneLink.split("/")[-3]
    workoutPath = "{0}/{1}_{2}.fit".format(oneOutputDir, str(oneYear), workoutId)
    logging.debug("Saving workout as {0}...".format(oneLink))
    with open(workoutPath, "wb") as file:
        file.write(dataFit.content)

    return True


if __name__ == "__main__":

    warmup(sys.argv)

    logging.info("-- --------------------------------------------------------------")
    logging.info("-- Begining of the program...")
    logging.info("-- --------------------------------------------------------------")

    customHeaders = {}
    customHeaders["Cookie"] = getAuthCookie()

    allWorkouts = {}
    rangeYears = range(CURRENT_YEAR, CURRENT_YEAR - MAX_PERIOD, -1)
    allWorkouts = getAllWorkouts(rangeYears, customHeaders)

    totalkWorkouts = 0
    for itemYear in allWorkouts:

        logging.info(
            "-- --------------------------------------------------------------"
        )
        seasonWorkouts = 0

        logging.info("Download all workouts for {0} season...".format(itemYear))
        yearPath = os.path.join(OUTPUT_DIR, str(itemYear))
        os.makedirs(yearPath, exist_ok=True)

        items = []

        for oneWorkout in allWorkouts[itemYear]:
            items.append(
                (
                    yearPath,
                    str(itemYear),
                    "{0}/export/fit".format(oneWorkout),
                    customHeaders,
                )
            )

        with multiprocessing.Pool() as pool:
            for result in pool.starmap(downloadWorkout, items):
                if result:
                    seasonWorkouts += 1
                    totalkWorkouts += 1

        logging.info(
            "{0} workouts downloaded for {1} season into {2}.".format(
                seasonWorkouts, itemYear, OUTPUT_DIR
            )
        )

    logging.info("-- --------------------------------------------------------------")
    logging.info("-- {0} workouts downloaded.".format(totalkWorkouts))
    logging.info("-- --------------------------------------------------------------")
    logging.info("-- End of the program.")
    logging.info("-- --------------------------------------------------------------")
