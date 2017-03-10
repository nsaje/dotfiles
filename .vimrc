set nocompatible              " be iMproved, required
filetype off                  " required


" set the runtime path to include Vundle and initialize
set rtp+=~/.vim/bundle/Vundle.vim
call vundle#begin()

" let Vundle manage Vundle, required
Plugin 'VundleVim/Vundle.vim'

" -------------------------------------------------------------------------------
"  PLUGINS
" -------------------------------------------------------------------------------

"Plugin 'zhaocai/GoldenView.Vim'

" JS
Plugin 'pangloss/vim-javascript.git'

" Git
Plugin 'tpope/vim-fugitive' " Git
autocmd QuickFixCmdPost *grep* cwindow

" file tree
Plugin 'scrooloose/nerdtree'
map <C-\> :NERDTreeToggle<CR>
let NERDTreeIgnore = ['\.pyc$']

" tag bar
Plugin 'majutsushi/tagbar'
nmap <F8> :TagbarToggle<CR>
let g:tagbar_foldlevel = 0
let g:tagbar_compact = 1

" fuzzy search
Plugin 'kien/ctrlp.vim'
nnoremap <A-p> :CtrlPBuffer<cr>
nnoremap <C-A-p> :CtrlPTag<cr>

Plugin 'scrooloose/nerdcommenter' " comment/uncomment
Plugin 'junegunn/goyo.vim' " zen writing mode

" writing
Plugin 'reedes/vim-pencil'
set nocompatible
augroup pencil
  autocmd!
  autocmd FileType markdown,mkd call pencil#init()
augroup END
let g:vim_markdown_folding_disabled = 1

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
" Trigger configuration. Do not use <tab> if you use https://github.com/Valloric/YouCompleteMe.
let g:UltiSnipsExpandTrigger="<tab>"
let g:UltiSnipsJumpForwardTrigger="<c-b>"
let g:UltiSnipsJumpBackwardTrigger="<c-z>"

" status bar
Plugin 'vim-airline/vim-airline'
Plugin 'vim-airline/vim-airline-themes'
" appear right away
set laststatus=2
if !exists('g:airline_symbols')
	let g:airline_symbols = {}
endif
let g:airline_powerline_fonts = 1
" unicode symbols
"let g:airline_left_sep = '»'
"let g:airline_left_sep = '▶'
"let g:airline_right_sep = '«'
"let g:airline_right_sep = '◀'
""let g:airline_left_sep = ''
""let g:airline_left_alt_sep = ''
""let g:airline_right_sep = ''
""let g:airline_right_alt_sep = ''
let g:airline_left_sep = ''
let g:airline_left_alt_sep = ''
let g:airline_right_sep = ''
let g:airline_right_alt_sep = ''
"let g:airline_symbols.branch = ''
"let g:airline_symbols.readonly = ''
"let g:airline_symbols.linenr = ''
" Enable the list of buffers
let g:airline#extensions#tabline#enabled = 1
let g:airline#extensions#tabline#show_buffers=2
" Show just the filename
let g:airline#extensions#tabline#fnamemod = ':t'

" theme
Plugin 'altercation/vim-colors-solarized'

Plugin 'qpkorr/vim-bufkill' " kill buffer with shortcut

" go
Plugin 'fatih/vim-go'
let g:go_fmt_command = "goimports"
let g:syntastic_go_checkers = ['golint', 'govet', 'errcheck']
let g:syntastic_mode_map = { 'mode': 'active', 'passive_filetypes': ['go'] }

" python
"Plugin 'nvie/vim-flake8'
Plugin 'klen/python-mode'
let g:pymode_rope_goto_definition_bind = "<C-]>"
let g:pymode_rope = 1
let g:pymode_options_max_line_length = 130
let g:pymode_folding = 0
let g:pymode_rope_regenerate_on_write = 0

" code completion
"Plugin 'valloric/youcompleteme'
"let g:ycm_add_preview_to_completeopt = 1
"let g:ycm_autoclose_preview_window_after_completion = 1
Plugin 'Shougo/deoplete.nvim'
Plugin 'zchee/deoplete-go'
Plugin 'zchee/deoplete-jedi'
let g:deoplete#enable_at_startup = 1
" auto-close preview window
autocmd InsertLeave * if pumvisible() == 0|silent! pclose|endif

" All of your Plugins must be added before the following line
call vundle#end()            " required
filetype plugin indent on    " required
filetype plugin on

" -------------------------------------------------------------------------------
"  LATE PLUGIN CONFIG
" -------------------------------------------------------------------------------

" theme
syntax enable
set background=light
colorscheme solarized


" ---------------------------------------------------------------------------------
"   ADDITIONAL CONFIG      
" ---------------------------------------------------------------------------------

" allow changing buffer without saving
set hidden

" comment out binding
nmap <C-_> <leader>c<Space>
vmap <C-_> <leader>c<Space>

" don't wrap long lines
set nowrap

" use mouse
set mouse=a

" display numbers
set nu

set wildignore+=*/tmp/*,*.so,*.swp,*.zip,*.pyc     " MacOSX/Linux

" close buffer
nnoremap <C-k> :BD<cr>

let &t_Co=256

" tabs
nnoremap <C-Left> :tabprev<CR>
nnoremap <C-Right> :tabnext<CR>
nnoremap <C-h> :bprev<CR>
nnoremap <C-l> :bnext<CR>

set nofoldenable
