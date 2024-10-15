:: set vars=21 24 27 30 33 36 39 42 45 48 51 54 57 60 129 255
set files="ryan98153/SmolLM-135M-fine-tuned2", "HuggingFaceTB/SmolLM-360M-Instruct"
:: set files="ryan98153/SmolLM-135M-fine-tuned2"
:: set files="HuggingFaceTB/SmolLM-360M-Instruct"
set nums= 3 4 1 5 6 7

: python .\remove-mistake.py "ryan98153/SmolLM-135M-fine-tuned2" 3

for %%n in (%nums%) do (
  for %%f in (%files%) do (
    python .\remove-mistake.py %%f %%n
  )
)