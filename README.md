# tauquest

This project contains the following packages:

 1. shell - contains a command line tool for asking questions:
    1.1. ask_questions.py - to run it prompt: python ask_questions.py
                            - note that it expects the files directory within the execution path that contains the following:
                                1. theta.npy (the output theta from the training execution)
                                2. courses.db
                                3. an example files directory is attached
 2. db - contains all the database related entities and executors for querying the database
 3. dto - contains all the entities in a non ORM data structure
 4. expression - contains classes which represent lambda-dcs expressions
 5. parser - contains raw data, and the script which create the database
 6. training - contains all the training related classes.
    6.1. main.py - to run the training prompt: python main.py