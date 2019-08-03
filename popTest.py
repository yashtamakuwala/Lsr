from subprocess import Popen, PIPE

Popen(['python3', 'Lsr.py', 'configA.txt'], stdout=PIPE, stderr=PIPE)
Popen(['python3', 'Lsr.py', 'configB.txt'], stdout=PIPE, stderr=PIPE)
Popen(['python3', 'Lsr.py', 'configC.txt'], stdout=PIPE, stderr=PIPE)
Popen(['python3', 'Lsr.py', 'configD.txt'], stdout=PIPE, stderr=PIPE)
Popen(['python3', 'Lsr.py', 'configE.txt'], stdout=PIPE, stderr=PIPE)
Popen(['python3', 'Lsr.py', 'configF.txt'], stdout=PIPE, stderr=PIPE)