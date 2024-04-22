" Vim syntax file
" Language: Velocity Template
" Maintainer: Asa Rentschler
" Latest Revision: April, 5, 2024
" Place this file in ~/.vim/syntax/ and add `au BufRead,BufNewFile *.vtmp set filetype=vtmp` to ~/.vimrc

if exists("b:current_syntax")
	finish
endif

" brackets
syn match codeBrackets '('
syn match codeBrackets ')'

" variable operator
syn match variableOperator '%'

" velocity variables
syn keyword velocityVariable __backend__ __base__ __distro__ __hash__ __name__ __system__ __tag__ __timestamp__

" velocity operatives
syn match velocityOperative '@'
syn match velocityOperative '|'

" backend contionals
syn match backendConditional '?\w*'

" section headers
syn match sectionHeader '@from'
syn match sectionHeader '@pre'
syn match sectionHeader '@arg'
syn match sectionHeader '@copy'
syn match sectionHeader '@run'
syn match sectionHeader '@env'
syn match sectionHeader '@label'
syn match sectionHeader '@entry'
syn match sectionHeader '@post'

" template variables
syn match templateVariable '[a-zA-Z0-9_]*' contained
syn region templateRegion start='(' end=')' contains=templateVariable

let b:current_syntax = "vtmp"

hi def link sectionHeader Function
hi def link backendConditional Conditional
hi def link velocityOperative Operator
hi def link velocityVariable Identifier
hi def link variableOperator Operator
hi def link codeBrackets Special
hi def link templateVariable Identifier
