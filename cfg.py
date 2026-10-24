"""Estruturas auxiliares do CFG da MicroC. Não substituem a AST."""

from __future__ import annotations

import load_previous  # Disponibiliza os módulos das etapas anteriores.

from dataclasses import dataclass, field

from ast_nodes import Expr, FunctionDecl, ReturnStmt, Stmt
from symbols import Scope


BlockId = int


@dataclass(frozen=True, slots=True)
class Jump:
    target: BlockId


@dataclass(frozen=True, slots=True)
class Branch:    #verifica uma condicao e define os dois possiveis destinos  (usar pra if e while)
    condition: Expr
    true_target: BlockId
    false_target: BlockId


@dataclass(frozen=True, slots=True)
class Return:  #conecta a saida por retorno
    statement: ReturnStmt


@dataclass(frozen=True, slots=True)
class Stop:
    """Terminador das saídas artificiais, que não possuem sucessores."""


Terminator = Jump | Branch | Return | Stop   #oq termina um BasicBlock e determina onde o fluxo vai depois


@dataclass(frozen=True, slots=True)
class ScopeExit:
    """Marca auxiliar, em ordem, para o fim da vida dos símbolos locais.

    Não é um novo nó da AST. As transferências e o verificador fornecidos
    removem os símbolos locais ao processar esta marca.
    """

    scope: Scope


Operation = Stmt | ScopeExit


@dataclass(slots=True)  #bloco basico do CFG, que vao ser ligados pelas arestas
class BasicBlock:
    id: BlockId
    operations: list[Operation] = field(default_factory=list)
    terminator: Terminator | None = None
    predecessors: set[BlockId] = field(default_factory=set)
    successors: set[BlockId] = field(default_factory=set)

    # None significa que o bloco ainda está aberto durante a construção.
    # Condições e expressões de retorno estão nos respectivos terminadores.


class CFG:  #grafo completo de uma funcao, vai contruir o grafo, quem vai passar os "comados" é o CFGBuilder
    def __init__(self, function: FunctionDecl) -> None:
        self.function = function  #funcao da AST que vai ser analisada
        self.blocks: dict[BlockId, BasicBlock] = {} #dicionario que vai guardar os blocos basicos
        self._next_id = 0 #quantidade de b locos

        self.entry = self.new_block().id  #entrada da funcao, self.entry guiarda somente o id
        self.return_exit = self.new_block().id #saida
        self.fallthrough_exit = self.new_block().id  #saida sem retorno

        self.terminate(self.return_exit, Stop())  #dps de return, n tem nenhum bloco
        self.terminate(self.fallthrough_exit, Stop()) #tbm n tem dps

    def new_block(self) -> BasicBlock:  #cria boloco basico
        block = BasicBlock(id=self._next_id)  #criando bloco e o id dele
        self.blocks[block.id] = block #add no dict
        self._next_id += 1 #++
        return block  #devolve bloco criado

    def _connect(self, source: BlockId, target: BlockId) -> None:  #aresta entre blocos
        """Atualize as duas pontas de uma aresta. Use terminate por fora."""

        self.blocks[source].successors.add(target)
        self.blocks[target].predecessors.add(source)

    def terminate(self, block_id: BlockId, terminator: Terminator) -> None: #fecha um bloco com um terminador,, recebe o bloco que queremos temrinar e como o bloco vai terminar
        """Feche um bloco e registre as arestas descritas pelo terminador.

        Todos os destinos precisam existir. A construção da forma do grafo,
        incluindo a escolha desses destinos, permanece no CFGBuilder.
        """

        block = self.blocks[block_id] #pega o bloco
        if block.terminator is not None:  #v c o bloco tem um terminator
            raise ValueError(f"o bloco {block_id} já possui terminador")
       #descobre o destino

        #variavel target tem os IDs dos blocos para os quais o bloco atual tem uma aresta
        if isinstance(terminator, Jump): #ao terminar bloco atual segue diretametne para o bloco alvo
            targets = (terminator.target,)
        #branch vai ter uma condicao e depois dois caminhos possiveis, um para caso seja V outro para  caso seja F
        elif isinstance(terminator, Branch): #verifica uma condicao e define os dois possiveis destinos  (usar pra if e while)
            targets = (terminator.true_target, terminator.false_target)
        elif isinstance(terminator, Return):  #
            targets = (self.return_exit,)
        elif isinstance(terminator, Stop):
            targets = ()
        else:
            raise TypeError(f"terminador desconhecido: {type(terminator).__name__}")

        for target in targets:  # v c os destinos existem
            if target not in self.blocks:
                raise ValueError(f"o bloco de destino {target} não existe")

        block.terminator = terminator #salva o terminator
        for target in targets:
            self._connect(block_id, target) #cria as arestas


def format_cfg(cfg: CFG) -> str:
    """Inspeção textual dos blocos existentes, inclusive os ainda abertos."""

    lines = [
        f"função {cfg.function.name}",
        f"entry=B{cfg.entry} return_exit=B{cfg.return_exit} "
        f"fallthrough_exit=B{cfg.fallthrough_exit}",
    ]
    for block_id, block in sorted(cfg.blocks.items()):
        lines.append(
            f"B{block_id}: pred={sorted(block.predecessors)} "
            f"succ={sorted(block.successors)}"
        )
        for operation in block.operations:
            if isinstance(operation, ScopeExit):
                lines.append("  ScopeExit")
            else:
                span = operation.span
                lines.append(
                    f"  {type(operation).__name__} "
                    f"em {span.start_line}:{span.start_column}"
                )
        lines.append(f"  terminador: {block.terminator!r}")
    return "\n".join(lines)
