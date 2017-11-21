#!bin/bash/python
# -*- coding: utf-8 -*-

"""
1. O programa deve funcionar em dois modos: sequencial e aleatório
2. No modo sequencial ele lê a criação de processos, alocação de memória e acessos seguindo uma lista de comandos conforme exemplo abaixo.
3. No modo aleatório o programa deve:
    a. O programa deve criar um conjunto de threads para simular processos executando. 
    b. Cada processo possui um tamanho, que representa quantos bytes ele ocupa na memória.
    c. O processo passa o tempo todo: solicitando acessos endereços aleatórios de memória.
4. O gerente de memória deve alocar o número de páginas para o processo, relativo ao tamanho do process.
5.  Para cada acesso, é necessário verificar se a página do processo onde aquele endereço se encontra, está ou não presente na memória.
    Se estiver o “acesso” é realizado sem problemas. Se não for, então o gerente de memória deve ser acionado e um “dump” da memória deve ser realizado,
    as tabelas de páginas dos processos, a situação da memória (que processo está ocupando cada página), e o endereço que gerou o page fault.
6. Deve haver alguma forma de acompanhar (visualizar) o que está acontecendo no programa a cada solicitação ou liberação.
 As informações de maneira manual (por arquivo) possui o seguinte formato (C de criar processo, A de acesso, M de alocar Memória):
Exemplo:
Modo: manual ou aleatório
Tamanho da página
Tamanho da memória física (múltiplo do tamanho das páginas)
Tamanho da área para armazenamento das páginas em disco
C|A|M processo tamanho|endereço|tamanho
Entregar código e documentação, conforme formato fornecido.

"""

import random
from collections import deque
from typing import List, Dict, Callable, Deque


class Manager(object):
    def __init__(self, algorithm: str, page_size: int, memory_size: int, swap_size: int) -> None:
        self.algorithm = algorithm
        self.page_size = page_size
        self.memory = Memory(page_size, memory_size)
        self.swap = Memory(page_size, swap_size)
        self.processes: Deque[str] = deque()
        self.operation: Dict[str, Callable[[str, int], None]] = {'C' : self.allocate}

    def use_process(self, process):
        self.processes.append(self.processes.pop(self.processes.index(process)))

    def get_lru_proc(self):
        return self.processes[0]

    def get_random_proc(self):
        return self.processes[random.randint(0, len(self.processes))]

    def allocate(self, proc_name: str, proc_size: int):
        pages_to_allocate = proc_size // self.page_size + (proc_size % self.page_size != 0)

        # find free blocks
        # write proc name on the appropriate blocks
        pass

    def process_orders(self, instructions_list: List[List[str]]):
        for instruct in instructions_list:
            instruct_type, proc_name, proc_size = instruct
            self.operation[instruct_type](proc_name, proc_size)
            break


class Memory(object):
    def __init__(self, page_size: int, number_of_bytes: int):
        self.page_size = page_size
        self.number_of_bytes = number_of_bytes
        self.physical = [['' for _ in range(page_size)] for _ in range(number_of_bytes)]
        self.used_pages: List[bool] = [False for _ in range(number_of_bytes // page_size)]

    def find_free_memory(self):
        pass


class Page(object):
    def __init__(self, size: int):
        self.size = size

def sublist_finder(mylist: list, pattern: list):
    """
    Thanks, Python's short-circuit evaluation.
    Pretty sure this could be made into a list comp, though.
    """
    matches = []
    for i in range(len(mylist)):
        if mylist[i] == pattern[0] and mylist[i:i+len(pattern)] == pattern:
            matches.append(i)
    return matches if len(matches) > 0 else None


def index_ifpossible(line: str, char: str):
    try:
        return line.index(char)
    except ValueError:
        return len(line)


def read_file(file_path: str) -> List[str]:
    with open(file_path) as setup_file:
        return list(setup_file)

testfile = [x[:index_ifpossible(x, '<')].strip()
            for x in read_file("input.txt") if x[0] not in {' ', '\n'}]
print(testfile)

mode = testfile[0]
algorithm_used = testfile[1]
page_size_in_bytes = int(testfile[2])
physical_memory_size_in_pages = int(testfile[3]) // page_size_in_bytes
swap_size_in_pages = int(testfile[4]) // page_size_in_bytes

instructions: List[List[str]] = [x.split(' ') for x in testfile[5:]]

