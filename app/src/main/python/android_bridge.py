# -*- coding: utf-8 -*-
"""Android adapter: original Windows +Milionaria Campeao V1 engine unchanged."""
import contextlib
from pathlib import Path
import milionaria_campeao_v1 as motor

class Progress:
    def __init__(self, path): self.path = Path(path)
    def write(self, s):
        if s:
            with self.path.open('a', encoding='utf-8') as f: f.write(s)
    def flush(self): pass

def run(history_file, output_dir):
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    log=out/'ANDAMENTO.txt'
    log.write_text('Iniciando leitura do historico +Milionaria...\n',encoding='utf-8')
    with contextlib.redirect_stdout(Progress(log)):
        history,rejected,duplicates=motor.read_history(history_file)
        print('Concursos validos:',len(history),'| rejeitadas:',len(rejected),'| duplicadas:',len(duplicates),flush=True)
        if len(history)<10:
            print('EXEMPLOS REJEITADOS:',rejected[:8],flush=True)
            raise ValueError('Menos de 10 concursos validos. Confira o TXT: concurso, seis dezenas e dois trevos.')
        stats=motor.analysis(history,out,rejected,duplicates)
        print('Auditoria concluida. Iniciando 15.890.700 combinacoes...',flush=True)
        best,processed,eligible=motor.select_game(stats)
        trevo_best,trevo_scores=motor.select_trevos(stats)
        if best[1] is None: raise ValueError('Nenhum jogo elegivel')
        (out/'RELATORIO_JOGO_V1.txt').write_text(
            '+MILIONARIA CAMPEAO V1\n'+
            'Concursos: '+str(len(history))+'\n'+
            'Combinacoes examinadas: '+str(processed)+'\n'+
            'Elegiveis: '+str(eligible)+'\n'+
            'Dezenas: '+str(best[1])+'\n'+
            'Trevos: '+str(trevo_best[1])+'\n'+
            'Score: '+str(best[0])+'\n'+
            'Ranking dos trevos: '+str(trevo_scores)+'\n',encoding='utf-8')
        print('CONCLUIDO! Dezenas:',best[1],'Trevos:',trevo_best[1],flush=True)
        return ','.join(map(str,best[1]))+'|'+','.join(map(str,trevo_best[1]))+'|'+str(len(history))+'|'+str(history[-1][0])+'|'+str(processed)+'|'+str(best[0])
