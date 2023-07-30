This folder contains the submission for the agent-based modelling project of the class SEN 1211 at TU Delft offered in Quarter 2, academic year 2022-2023.

The authors are aware that the present file slightly exceeds the 100MB submission limit - this is due to the voluminous output produced by mesa in order to comply with other of the project directives - we are aware of no readily available alternative short of modifying the mesa source code, deemed too tangential to the work at hand.  With our apologies, it is hoped that this will be forgiven.



Per instructions, the files constituting the operational model are located in the 'model' folder.

A PDF file of the report is preserved in the main directory.

Output of the model is saved as '.pickle' files under the 'output' folder - in the case of one of these experiments, these files were broken up into five parts (one for each run) due to working-memory limitations.

The final plots used in the body of the report are saved in the 'analysis' folder, along with the post-processing script which created them.

The figures in the appendix of the report are generated from mesa itself - the code generating which was deprecated, but may be found commented out in the 'main.py' file of the model folder.

The 'base_mesa_model' and '__pycache__' folders are not pertinent to the report, but contain some data which may be necessary to reduplicate its conclusions (at least by the authors' current minimal understanding of anaconda's packaging system); thus they are included 'just in case'.


NB: the default output format of mesa saved in the pickle files is extremely clunky, and requires a good deal of memory and trail-error in order for the post-processing to work.

Please send an email to CharlesRW@protonmail.com if there are any questions or unexpected issues :)
