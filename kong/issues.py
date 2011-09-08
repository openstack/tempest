import re


class KnownIssuesFinder(object):
    
    def __init__(self):
        self.count = 0
        self._pattern = re.compile('# *KNOWN-ISSUE')

    def find_known_issues(self, package):
        for file in self._find_test_module_files(package):
            self._count_known_issues(file)
                
    def _find_test_module_files(self, package):
        for name in dir(package):
            if name.startswith('test'):
                module = getattr(package, name)
                yield module.__file__

    def _count_known_issues(self, file):
        if file.endswith('.pyc') or file.endswith('.pyo'):
            file = file[0:-1]
        for line in open(file):
            if self._pattern.search(line) is not None:
                self.count += 1
