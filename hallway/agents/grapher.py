from hallway.common.runtime import run
PROMPT = 'You are Grapher. HANDOFF phase 1 has no approved/research room implementation. Do not act on case transcripts. No downstream execution is authorized. Stop without claiming integration success.'
if __name__ == "__main__": run('grapher',PROMPT)
