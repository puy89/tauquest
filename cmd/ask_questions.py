import sys
import numpy as np
from training.lexicon import Lexicon
from training.main import DBCache
from training.questions_answers_trainer import QuestionsAnswersTrainer


def main(argv):
    db_cache = DBCache()
    lexicon = Lexicon()
    lexicon.update_lexicon(db_cache)
    theta = np.load("files/theta.npy")
    trainer = QuestionsAnswersTrainer(db_cache, lexicon.lexicon)

    while True:
        input = raw_input("Ask a question")
        if input is "exit":
            exit(0)
        try:
            results = trainer.eval(input, theta=theta)
            if len(results) == 0:
                print("Sorry, couldn't find any results for this question")
                continue
            print("\tHere are the results")
            for result in results:
                print("\t\t{0}".format(result))

        except Exception as e:
            print("\tSorry, couldn't answer this question")


if __name__ == '__main__':
    main(sys.argv)