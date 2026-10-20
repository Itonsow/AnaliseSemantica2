"""Construa um CFG auxiliar por função, preservando os nós da AST."""

from __future__ import annotations

import load_previous  # Disponibiliza os módulos das etapas anteriores.

from ast_nodes import Block, FunctionDecl, IfStmt, Stmt, WhileStmt
from cfg import BlockId, CFG, Jump

#um bloco básico agrupa operações sequenciais até encontrar uma mudança no fluxo de controle
class CFGBuilder:
    def build(self, function: FunctionDecl) -> CFG:
        self.cfg = CFG(function)  #cria um grafo pra funcao
        body_entry = self.cfg.new_block()  #cria um bloco #id == 3
        self.cfg.terminate(self.cfg.entry, Jump(body_entry.id))
        continuation = self._build_block(function.body, body_entry.id) #percorrer a AST e contruir o fluxo.... funcition.body - block da AST
        #continuation vai receber um ID do bloco do CFG que ainda esta aberto depois de percorrer o corpo
        if continuation is not None:  #escopos diferentes podem continuar no mesmo bloco pq são sequenciais
            self.cfg.terminate(continuation, Jump(self.cfg.fallthrough_exit)) 
        return self.cfg  #retorna grafo contruido

    def _build_block(self, block: Block, current: BlockId) -> BlockId | None:   #recebe bloco da AST, ID do bloco
        """Percorra um bloco da AST e devolva sua continuação normal.
        `current` identifica um bloco básico aberto. Comandos sequenciais
        permanecem nele. Comandos de controle podem mudar a continuação.
        None indica que os caminhos deste bloco não alcançam o próximo comando.
        """
        for statement in block.statements:
            if current is None:
                break
            current = self._build_statement(statement, current) #comando da AST que build_state vai tratar e o ID do bloco 

        #quando chega no fim das chaves, pega o fim das cheves de scopo(bloco)
        if current is not None:
            scope = block.metadata["scope"] #pega o escopo guardado do name resolver
            cfg_block = self.cfg.blocks[current]
            cfg_block.operations.append(ScopeExit(scope)) #adiciona na lista

        return current

    def _build_statement(self, statement: Stmt, current: BlockId) -> BlockId | None: #coloca declarações, atri, chamadas,etc no CFG
        if isinstance(statement, Block):  #ve c é um bloco de chaves da AST
            return self._build_block(statement, current) #se for, chama de volta o build_block

        if isinstance(statement, VarDecl): #verifica se o statement pertence a uma classe de varaivel
            cfg_block = self.cfg.blocks[current] #pega o bloco atual do CFG que esta
            cfg_block.operations.append(statement) #coloca na lista de operacoes do bloco
            return current #retorna o id do bloco

        if isinstance(statement, Assignment):  #verifica se o statement pertence a uma classe de atribuicao
            cfg_block = self.cfg.blocks[current] #pega o ID
            cfg_block.operations.append(statement) #add
            return current

        if isinstance(statement, PrintStmt):  #verifica se o statement pertence a uma classe print
            cfg_block = self.cfg.blocks[current] #pega o ID
            cfg_block.operations.append(statement) #add
            return current

        if isinstance(statement, CallStmt):  #verifica se o statement pertence a uma classe chamada de funcao
            cfg_block = self.cfg.blocks[current] #pega o ID
            cfg_block.operations.append(statement) #add
            return current

        if isinstance(statement, ReturnStmt): #verifica se o statement pertence a uma classe retorno
            self.cfg.terminate(current, Return(statement))# Define o retorno como o terminate
            return None #devolve None, n continua para o proximo comando

        if isinstance(statement, IfStmt):
            return self._build_if(statement, current)

        if isinstance(statement, WhileStmt):
            return self._build_while(statement, current)
        

    def _build_if(self, statement: IfStmt, current: BlockId) -> BlockId | None: #crua os caminhos verdadeiro e falso
        then_entry = self.cfg.new_block() #cria um novo bloco para o caminho verdadeiro
        else_entry = self.cfg.new_block() #cria outro para o falso

        branch = Branch(statement.condition, then_entry.id, else_entry.id) #coloca me branch a condição, e os dois ID, do falso e do verdadeiro
        self.cfg.terminate(current, branch) # coloca o branch como terminador e registra os dois caminhos

        then_continuation = self._build_block(statement.then_block, then_entry.id) #pega oq tem dentro do caminho e coloca no bloco entry
        if statement.else_block is not None: #verifica se tem else
            else_continuation = self._build_block(statement.else_block, else_entry.id) #se tiver, coloca as intruções dentro do blco
        else:
            else_continuation = else_entry.id

        if then_continuation is None and else_continuation is None: #se caso ambos tiverem return como opção, retorna None, n tem como contiunuar
            return None

        continuation = self.cfg.new_block() #novo bloco para as duas possibilidades de caminhos, tanto verdaderio quanto falso
        if then_continuation is not None: #caso n acabe na condicao(n tenha um return) vai pro prox bloco
            self.cfg.terminate(then_continuation, Jump(continuation.id))
        if else_continuation is not None:
            self.cfg.terminate(else_continuation, Jump(continuation.id))

        return continuation.id #retorna o ID do bloco na seuqnacia dos blocos de condicao

    def _build_while(self, statement: WhileStmt, current: BlockId) -> BlockId | None: #cria o teste, o corpo e a volta do laço
        """TODO: construa o fluxo do laço e devolva sua continuação."""

        raise NotImplementedError("implemente CFGBuilder._build_while")
