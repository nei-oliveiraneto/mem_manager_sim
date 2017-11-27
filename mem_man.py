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
from itertools import chain
from typing import List, Dict, Callable, Deque, Tuple


class Manager(object):
    def __init__(self, algorithm: str, page_size: int, memory_size: int, swap_size: int) -> None:
        """

        :param algorithm:
        :param page_size: in bytes
        :param memory_size: in pages
        :param swap_size:
        """
        self.scheduling_algorithm = algorithm
        self.page_size = page_size
        self.memory = Memory(page_size, memory_size)
        self._swap = Memory(page_size, swap_size)
        self.processes: Deque[str] = deque()
        self.algorithm: Dict[str, Callable[..., str]] = {'lru': self.get_lru_proc}
        self.operation: Dict[str, Callable[[str, int], None]] = {
            'C' : self.first_alloc, 'A' : self.access, 'M' : self.malloc}

    def use_process(self, process: str):
        index = self.processes.index(process)
        self.processes.append(self.processes[index])
        del self.processes[index]

    def get_lru_proc(self):
        return self.processes[0]

    def get_random_proc(self):
        return self.processes[random.randint(0, len(self.processes))]

    def swap(self, proc_name: str) -> List[int]:
        """Swap proc's earliest page from memory to storage."""
        # find all indices of proc pages in memory
        page, indices = self.memory.get_allocated_indices_from_earliest_page(proc_name)
        free_pages = self._swap.find_free_pages()
        if len(free_pages) > 0:
            self._swap.physical[free_pages[0]] = [proc_name] * len(indices)
            self.memory.physical[page] = ['  '] * 8 + [proc_name] * (8 - len(indices))
        else:
            print("Out of swap storage.")
        # put them in storage
        # free memory
        # return indices of freed memory
        return page

    def alloc(self, proc_name: str, proc_size: int):
        pass

    def get_alloc_requirements(self, alloc_size: int) -> Tuple[int, int]:
        """
        :param alloc_size: allocation size in bytes from zero.
        :return: Tuple[bytes to allocate in the next page, whole pages to allocate]
        """
        return (alloc_size % self.page_size, alloc_size // self.page_size)

    def first_alloc(self, proc_name: str, proc_size: int) -> None:
        self.processes.append(proc_name)

        extra_bytes, whole_pages_to_allocate = self.get_alloc_requirements(proc_size)
        free_pages = self.memory.find_free_pages()

        if len(free_pages) < whole_pages_to_allocate + (extra_bytes != 0):
            print("Not enough memory. Swapping...")
            chosen_proc_to_swap: str = self.algorithm[self.scheduling_algorithm]()
            free_pages = self.swap(chosen_proc_to_swap)

        pages_to_use = free_pages[:whole_pages_to_allocate + 1]
        # write process name onto the first pages_to_allocate pages
        self.memory.alloc(pages_to_use, extra_bytes, proc_name)

    def access(self, proc_name: str, byte_to_access: int) -> None:
        if (proc_name, byte_to_access) in self.memory:
            self.use_process(proc_name)
            print("Accessed {}'s byte number {}. Physical address {}.".format(
                proc_name, byte_to_access, self.memory.get_physical_address((proc_name, byte_to_access))))
        elif (proc_name, byte_to_access) in self._swap:
            print("{}'s page {} was not found in memory. PAGE FAULT!")
        else:
            print("Access error: {}:({}:{}]".format(
                proc_name, self.memory.get_last_virtual_index(proc_name), byte_to_access))

    def malloc(self, proc_name: str, new_bytes: int):
        self.use_process(proc_name)  # what if proc is not in memory?

        last_byte = self.memory.get_last_virtual_index(proc_name)
        hanging_bytes = last_byte % self.page_size
        last_page = -1 if not hanging_bytes else self.memory.get_physical_address((proc_name, last_byte - 1))[0]
        if new_bytes < self.page_size and new_bytes + hanging_bytes < self.page_size:
            self.memory.malloc([], proc_name, last_page,
                self.memory.find_free_indices(last_page),
                up_to_vbyte=last_byte + new_bytes
            )
        else:
            # snippet I could turn into a method
            extra_bytes, whole_pages_to_allocate = self.get_alloc_requirements(new_bytes)
            free_pages = self.memory.find_free_pages()


            if len(free_pages) < whole_pages_to_allocate + (extra_bytes != 0):
                print("Not enough memory. Swapping...")
                chosen_proc_to_swap: str = self.algorithm[self.scheduling_algorithm]()
                free_pages = self.swap(chosen_proc_to_swap)

            pages_to_use = free_pages[:whole_pages_to_allocate + 1]
            # close snippet

            self.memory.malloc(pages_to_use, proc_name, last_page,
                self.memory.find_free_indices(last_page),
                up_to_vbyte=last_byte + new_bytes
            )

    def process_orders(self, instructions_list: List[List[str]]) -> None:
        for instruct in instructions_list:
            instruct_type, proc_name, proc_size = instruct
            print(instruct, self.memory.physical)
            self.operation[instruct_type](proc_name, int(proc_size))


class Memory(object):
    def __init__(self, page_size: int, pages_in_memory: int):
        self.physical: List[List[str]] = [['  ' for _ in range(page_size)] for _ in range(pages_in_memory)]
        self.used_pages: List[bool] = [False for _ in range(pages_in_memory)]
        self.last_virtual_index_by_proc: Dict[str, int] = {}
        self.virtual_indices: Dict[Tuple[str, int], Tuple[int, int]] = {}
        self.page_size = page_size
        self.number_of_bytes = pages_in_memory * self.page_size

    def get_last_virtual_index(self, proc_name: str) -> int:
        return self.last_virtual_index_by_proc[proc_name]

    def get_physical_address(self, proc_vbyte: Tuple[str, int]) -> Tuple[int, int]:
        return self.virtual_indices[proc_vbyte]

    def find_free_indices(self, page_index: int):
        return [i for i, byte in enumerate(self.physical[page_index]) if byte == '  ']

    def find_free_pages(self) -> List[int]:
        return [i for i, used in enumerate(self.used_pages) if not used]

    def get_all_phys_indices(self, proc_name: str) -> List[Tuple[int, int]]:
        return [self.virtual_indices[(proc_name, i)] for i in range(self.get_last_virtual_index(proc_name))]

    def get_allocated_indices_from_earliest_page(self, proc_name: str) -> Tuple[int, List[int]]:
        physical_indices = self.get_all_phys_indices(proc_name)
        earliest_page_index = physical_indices[0][0]
        i = 0
        indices_used_by_process_inside_page = []
        while physical_indices[i] == earliest_page_index:
            indices_used_by_process_inside_page.append(physical_indices[i][1])
        return (earliest_page_index, indices_used_by_process_inside_page)

    def update_last_virtual_index(self, proc_name: str, last_byte: int):
        self.last_virtual_index_by_proc.update({proc_name : last_byte})

    def toogle_in_bitmap(self, page_indices: List[int]):
        for i in page_indices:
            self.used_pages[i] = not self.used_pages[i]

    def update_virtual_indices(self, proc_name: str, page_indices: List[int],
                               extra_bytes: int, last_virtual_index: int=0):
        virtual_addresses = range(
            last_virtual_index,(len(page_indices) - 1) * self.page_size + last_virtual_index)
        physical_addresses = list(range(self.page_size)) * (len(page_indices) - 1)
        page_num = chain(*[[x] * self.page_size for x in page_indices[:-1]])

        self.virtual_indices.update(
            {(proc_name, virtual_i) : (page_index, physical_index)
             for virtual_i, physical_index, page_index in zip(virtual_addresses, physical_addresses, page_num)}
        )

        last_virtual_index += (len(page_indices) - 1) * self.page_size

        if extra_bytes:
            self.virtual_indices.update(
                {(proc_name, virtual_i) : (page_indices[-1], physical_index)
                 for virtual_i, physical_index in zip(
                    range(last_virtual_index, last_virtual_index + extra_bytes),
                    range(self.page_size))}
            )

    def alloc(self, page_indices: List[int], amount_of_extra_bytes: int, value_to_assign: str):
        self.update_last_virtual_index(
            value_to_assign, (len(page_indices) - 1) * self.page_size + amount_of_extra_bytes)
        self.toogle_in_bitmap(page_indices if amount_of_extra_bytes else page_indices[:-1])
        self.update_virtual_indices(value_to_assign, page_indices, amount_of_extra_bytes)

        # Add another element to page_indices if the last free page is the last physical page
        # So I can always take one page off of the end.
        if page_indices[-1] == len(self.used_pages) - 1:
            page_indices.append(None)

        for i in page_indices[:-1]:
            self.physical[i] = [value_to_assign] * self.page_size
        for i in range(amount_of_extra_bytes):
            self.physical[page_indices[-1]][i] = value_to_assign

    def malloc(self, pages: List[int], proc_name: str, last_page: int, free_indices: List[int], up_to_vbyte: int):
        last_vindex = self.get_last_virtual_index(proc_name)

        if last_page == -1 and len(free_indices) == 0:
            # When no incomplete page is provided, just

            if pages[-1] == len(self.used_pages) - 1:
                pages.append(None)
            for i in pages[:-1]:
                self.physical[i] = [proc_name] * self.page_size
            for i in range(up_to_vbyte):
                self.physical[pages[-1]][i] = proc_name

        elif up_to_vbyte - last_vindex < len(free_indices):
            # When allocation fits inside remaining bytes on the incomplete page
            for i in free_indices[:up_to_vbyte - last_vindex]:
                self.physical[last_page][i] = proc_name

            self.update_virtual_indices(
                proc_name, [last_page], len(free_indices), last_virtual_index=last_vindex)
        else:
            for i in free_indices:
                self.physical[last_page][i] = proc_name

            self.update_virtual_indices(
                proc_name, [last_page], len(free_indices), last_virtual_index=last_vindex)

            if pages[-1] == len(self.used_pages) - 1:
                pages.append(None)
            for i in pages[:-1]:
                self.physical[i] = [proc_name] * self.page_size
            for i in range(up_to_vbyte % self.page_size):
                print(i)
                self.physical[pages[-1]][i] = proc_name

            self.update_virtual_indices(
                proc_name, pages, up_to_vbyte % self.page_size, last_virtual_index=last_vindex)
            self.toogle_in_bitmap(pages if up_to_vbyte % self.page_size else pages[:-1])

        self.update_last_virtual_index(proc_name, up_to_vbyte)
        pass

    def __contains__(self, proc_vbyte: Tuple[str, int]) -> bool:
        return proc_vbyte in self.virtual_indices

    def __str__(self) -> str:
        s = ''
        for i in self.physical:
            s += str(i)+'\n'
        return s

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

mode = testfile[0]
algorithm_used = testfile[1]
page_size_in_bytes = int(testfile[2])
physical_memory_size_in_pages = int(testfile[3]) // page_size_in_bytes
swap_size_in_pages = int(testfile[4]) // page_size_in_bytes

instructions: List[List[str]] = [x.split(' ') for x in testfile[5:]]

a = Manager(algorithm_used, page_size_in_bytes, physical_memory_size_in_pages, swap_size_in_pages)

# a.process_orders([['C', 'p1', '16']])
a.process_orders(instructions[:11])
# a.process_orders([['M', 'p1', '8']])
print(a.memory.physical)
print(a.memory.virtual_indices, sep='\n')
