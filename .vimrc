set nocompatible              " be iMproved, required
filetype off                  " required

" set the runtime path to include Vundle and initialize
set rtp+=~/.vim/bundle/Vundle.vim
call vundle#begin()
" alternatively, pass a path where Vundle should install plugins
"call vundle#begin('~/some/path/here')

" let Vundle manage Vundle, required
Plugin 'VundleVim/Vundle.vim'

Plugin 'tpope/vim-fugitive' " Git
Plugin 'scrooloose/nerdtree' " file tree
Plugin 'majutsushi/tagbar' " tag bar
Plugin 'kien/ctrlp.vim' " fuzzy search
Plugin 'scrooloose/nerdcommenter' " comment/uncomment
Plugin 'junegunn/goyo.vim' " zen writing mode
Plugin 'reedes/vim-pencil' " writing
Plugin 'scrooloose/syntastic' " syntax checking
Plugin 'avakhov/vim-yaml' " yaml support
"Plugin 'tpope/vim-sleuth' " automatic indentation settings
"Plugin 'godlygeek/tabular' " aligning things
"Plugin 'plasticboy/vim-markdown' " markdown (mostly for tables: :TableFormat)
Plugin 'airblade/vim-gitgutter' " git status in gutter
Plugin 'tpope/vim-surround' " surrounding

" snippets
Plugin 'SirVer/ultisnips'
Plugin 'honza/vim-snippets'

" status bar
Plugin 'vim-airline/vim-airline'
Plugin 'vim-airline/vim-airline-themes'

Plugin 'altercation/vim-colors-solarized' " themes
Plugin 'qpkorr/vim-bufkill' " kill buffer with shortcut

" go
Plugin 'fatih/vim-go'

" python
"Plugin 'nvie/vim-flake8'
Plugin 'klen/python-mode'
let g:pymode_rope_goto_definition_bind = "<C-]>"

" code completion
 "Plugin 'valloric/youcompleteme'
Plugin 'Shougo/deoplete.nvim'
Plugin 'zchee/deoplete-go'
Plugin 'zchee/deoplete-jedi'



" allow changing buffer without saving
set hidden

" comment out binding
nmap <C-_> <leader>c<Space>
vmap <C-_> <leader>c<Space>

" dont wrap
set nowrap

" All of your Plugins must be added before the following line
call vundle#end()            " required
filetype plugin indent on    " required
" To ignore plugin indent changes, instead use:
"filetype plugin on
"
" Brief help
" :PluginList       - lists configured plugins
" :PluginInstall    - installs plugins; append `!` to update or just :PluginUpdate
" :PluginSearch foo - searches for foo; append `!` to refresh local cache
" :PluginClean      - confirms removal of unused plugins; append `!` to auto-approve removal
"
" see :h vundle for more details or wiki for FAQ
" Put your non-Plugin stuff after this line

" use mouse
set mouse=a

" display numbers
set nu

" fugitive options
" open quickfix after grep
autocmd QuickFixCmdPost *grep* cwindow

" nerdtree binding
map <C-\> :NERDTreeToggle<CR>
let NERDTreeIgnore = ['\.pyc$']

" tagbar binding
nmap <F8> :TagbarToggle<CR>
"let g:tagbar_foldlevel = 0
"let g:tagbar_compact = 1

" ctags ctrlp binding
nnoremap <A-p> :CtrlPBuffer<cr>
nnoremap <C-A-p> :CtrlPTag<cr>

set wildignore+=*/tmp/*,*.so,*.swp,*.zip,*.pyc     " MacOSX/Linux

" close buffer
nnoremap <C-k> :BD<cr>

" theme
syntax enable
set background=light
colorscheme solarized

let &t_Co=256

" airline config
" appear right away
set laststatus=2
if !exists('g:airline_symbols')
	let g:airline_symbols = {}
endif
"let g:airline_left_sep = ''
"let g:airline_left_alt_sep = ''
"let g:airline_right_sep = ''
"let g:airline_right_alt_sep = ''
let g:airline_left_sep = ''
let g:airline_left_alt_sep = '<'
let g:airline_right_sep = ''
let g:airline_right_alt_sep = '>'
let g:airline_symbols.branch = ''
let g:airline_symbols.readonly = ''
let g:airline_symbols.linenr = ''
" Enable the list of buffers
let g:airline#extensions#tabline#enabled = 1
let g:airline#extensions#tabline#show_buffers=2
" Show just the filename
let g:airline#extensions#tabline#fnamemod = ':t'

" tabs
nnoremap <C-Left> :tabprev<CR>
nnoremap <C-Right> :tabnext<CR>
nnoremap <C-h> :bprev<CR>
nnoremap <C-l> :bnext<CR>

" pencil
set nocompatible
" filetype plugin on       " may already be in your .vimrc
augroup pencil
  autocmd!
  autocmd FileType markdown,mkd call pencil#init()
augroup END

let g:vim_markdown_folding_disabled = 1

let g:go_fmt_command = "goimports"
let g:syntastic_go_checkers = ['golint', 'govet', 'errcheck']
let g:syntastic_mode_map = { 'mode': 'active', 'passive_filetypes': ['go'] }

" youcompleteme
"let g:ycm_add_preview_to_completeopt = 1
"let g:ycm_autoclose_preview_window_after_completion = 1

" deoplete
let g:deoplete#enable_at_startup = 1

" AUTO-CLOSE PREVIEW WINDOW (scratch)
" If you prefer the Omni-Completion tip window to close when a selection is
" made, these lines close it on movement in insert mode or when leaving
" insert mode
"autocmd CursorMovedI * if pumvisible() == 0|silent! pclose|endif
autocmd InsertLeave * if pumvisible() == 0|silent! pclose|endif

" snippets config
" Trigger configuration. Do not use <tab> if you use https://github.com/Valloric/YouCompleteMe.
let g:UltiSnipsExpandTrigger="<tab>"
let g:UltiSnipsJumpForwardTrigger="<c-b>"
let g:UltiSnipsJumpBackwardTrigger="<c-z>"

set nofoldenable
