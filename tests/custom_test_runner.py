import time
import unittest
from colorama import Fore, Style


class CustomTestResult(unittest.TestResult):
    def startTest(self, test):
        self.start_time = time.time()
        super().startTest(test)
        print(Fore.BLUE + f"\n# Starting {test}" + Style.RESET_ALL)

    def stopTest(self, test):
        super().stopTest(test)
        print(Fore.LIGHTBLUE_EX + f" -> 🏁 Finished {test}" + Style.RESET_ALL)
        print(
            Fore.LIGHTBLACK_EX
            + f" -> ⏱️ Execution time {time.time() - self.start_time} seconds"
            + Style.RESET_ALL
        )

    def addSuccess(self, test):
        super().addSuccess(test)
        print(Fore.GREEN + f"\n -> Test: {test} ✅ PASSED" + Style.RESET_ALL)

    def addFailure(self, test, err):
        super().addFailure(test, err)
        print(Fore.RED + f"\n -> Test: {test} ⛔ FAILED" + Style.RESET_ALL)


class CustomTextTestRunner(unittest.TextTestRunner):
    resultclass = CustomTestResult

    def run(self, test):
        result = super().run(test)
        if result.wasSuccessful():
            print(Fore.GREEN + f"\n# Test {test} PASSED" + Style.RESET_ALL)
        else:
            print(Fore.RED + f"\n# Test {test} FAILED" + Style.RESET_ALL)
        return result
