" Vim syntax file
" Language: Velocity Template
" Maintainer: Asa Rentschler
" Latest Revision: September, 19, 2024
" Velocity Version: 0.1
" Place this file in ~/.vim/syntax/ and add `au BufRead,BufNewFile *.vtmp set filetype=vtmp` to ~/.vimrc

if exists("b:current_syntax")
        finish
endif

" comments
syn match codeComment '>>>.*'

" velocity variables
syn keyword velocityVariable __backend__ __base__ __distro__ __name__ __system__ __version__ __timestamp__

" velocity operatives
syn match velocityOperative '|'
syn match velocityOperative '!envar'

" section headers
syn match sectionHeader '@from'
syn match sectionHeader '@pre'
syn match sectionHeader '@copy'
syn match sectionHeader '@run'
syn match sectionHeader '@env'
syn match sectionHeader '@label'
syn match sectionHeader '@entry'
syn match sectionHeader '@post'

" contained sections
syn match templateVariable '[a-zA-Z0-9_]*' contained
syn match argumentName '[a-zA-Z0-9_]*' contained
syn match conditionalArrow '|>' contained

syn region variableRegion matchgroup=velocityOperative start="{{" end="}}" contains=templateVariable
syn region argumentRegion matchgroup=velocityOperative start="@@" end="@@" contains=argumentName
syn region conditionalRegion matchgroup=velocityOperative start="??" end="??" contains=conditionalArrow

let b:current_syntax = "vtmp"

hi def link codeComment Comment
hi def link sectionHeader Function
hi def link velocityOperative Operator
hi def link velocityVariable Identifier
hi def link templateVariable Identifier
hi def link argumentName Identifier
hi def link conditionalArrow Operator