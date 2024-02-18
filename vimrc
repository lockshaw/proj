augroup lockshaw_cpp
  autocmd!
  autocmd FileType cpp set tabstop=2 shiftwidth=2 expandtab
  autocmd FileType cpp set cino+=g0
augroup END

augroup lockshaw_bash
  autocmd!
  autocmd FileType sh set tabstop=2 shiftwidth=2 expandtab
augroup END

augroup lockshaw_vimscript
  autocmd!
  autocmd FileType vim set tabstop=2 shiftwidth=2 expandtab
augroup END

augroup lockshaw_cmake
  autocmd!
  autocmd FileType cmake set tabstop=2 shiftwidth=2 expandtab
augroup END

function! FixTerm() 
  1Tkill
  1Tclear!
endfunction

function! RunCmake()
  call FixTerm()
  exec '1T clear && proj cmake'
endfunction

function! Build()     
  call FixTerm()
  exec '1T clear && proj build'
endfunction 

function! Test()
  call FixTerm()
  exec '1T clear && proj test'
endfunction

function! GetMyPath()
  return fnamemodify(resolve(expand('<script>:p')), ':h')
endfunction

let s:snippets_dir = GetMyPath() .. '/snippets/'
let g:UltiSnipsEditSplit = "context"
let g:UltiSnipsSnippetStorageDirectoryForUltiSnipsEdit = s:snippets_dir
let g:UltiSnipsSnippetDirectories=[s:snippets_dir]
let g:UltiSnipsExpandTrigger = '<c-g>'
" let g:UltiSnipsExpandTrigger = "<tab>"
let g:UltiSnipsListSnippets = "<c-tab>"
let g:UltiSnipsJumpForwardTrigger = "<c-f>"
let g:UltiSnipsJumpBackwardTrigger = "<c-F>"

nnoremap BB :call Build()<CR>
nnoremap TT :call Test()<CR>
command! RunCmake :call RunCmake()
" command! Fix :call Fix()
" nnoremap <leader>f :call Fix()<CR>
