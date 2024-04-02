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

nnoremap BB :call Build()<CR>
nnoremap TT :call Test()<CR>
command! RunCmake :call RunCmake()

" let g:UltiSnipsEditSplit = "context"
" let g:UltiSnipsSnippetStorageDirectoryForUltiSnipsEdit = s:snippets_dir
" let g:UltiSnipsSnippetDirectories=[s:snippets_dir]
" let g:UltiSnipsExpandTrigger = '<c-g>'
" let g:UltiSnipsExpandTrigger = "<tab>"
" let g:UltiSnipsListSnippets = "<c-tab>"
" let g:UltiSnipsJumpForwardTrigger = "<c-f>"
" let g:UltiSnipsJumpBackwardTrigger = "<c-F>"
