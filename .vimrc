set nocompatible              " be iMproved, required
filetype off                  " required

" set the runtime path to include Vundle and initialize
set rtp+=~/.vim/bundle/Vundle.vim
call vundle#begin()
" alternatively, pass a path where Vundle should install plugins
"call vundle#begin('~/some/path/here')

" let Vundle manage Vundle, required
Plugin 'VundleVim/Vundle.vim'

Plugin 'tpope/vim-fugitive'
Plugin 'scrooloose/nerdtree'
Plugin 'kien/ctrlp.vim'
Plugin 'vim-airline/vim-airline'
Plugin 'vim-airline/vim-airline-themes'
Plugin 'altercation/vim-colors-solarized'
Plugin 'fatih/vim-go'
Plugin 'scrooloose/syntastic'
" Plugin 'valloric/youcompleteme'
" Plugin 'dkprice/vim-easygrep'
Plugin 'nvie/vim-flake8'
Plugin 'avakhov/vim-yaml'
Plugin 'scrooloose/nerdcommenter'
Plugin 'junegunn/goyo.vim'
Plugin 'reedes/vim-pencil'
Plugin 'tpope/vim-sleuth' " automatic indentation settings


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

" nerdtree binding
map <C-\> :NERDTreeToggle<CR>

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
let g:airline_left_sep = ''
let g:airline_left_alt_sep = ''
let g:airline_right_sep = ''
let g:airline_right_alt_sep = ''
let g:airline_symbols.branch = ''
let g:airline_symbols.readonly = ''
let g:airline_symbols.linenr = ''
" Enable the list of buffers
let g:airline#extensions#tabline#enabled = 1
let g:airline#extensions#tabline#show_buffers=2
" Show just the filename
let g:airline#extensions#tabline#fnamemod = ':t'

" tabs
nnoremap <C-Left> :bprev<CR>
nnoremap <C-Right> :bnext<CR>
nnoremap <C-h> :bprev<CR>
nnoremap <C-l> :bnext<CR>

" pencil
set nocompatible
" filetype plugin on       " may already be in your .vimrc
augroup pencil
  autocmd!
  autocmd FileType markdown,mkd call pencil#init()
  autocmd FileType text         call pencil#init()
augroup END
