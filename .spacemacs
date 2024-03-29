;; -*- mode: emacs-lisp -*-
;; This file is loaded by Spacemacs at startup.
;; It must be stored in your home directory.

(defun dotspacemacs/layers ()
  "Configuration Layers declaration.
You should not put any user code in this function besides modifying the variable
values."
  (setq-default
   ;; Base distribution to use. This is a layer contained in the directory
   ;; `+distribution'. For now available distributions are `spacemacs-base'
   ;; or `spacemacs'. (default 'spacemacs)
   dotspacemacs-distribution 'spacemacs
   ;; Lazy installation of layers (i.e. layers are installed only when a file
   ;; with a supported type is opened). Possible values are `all', `unused'
   ;; and `nil'. `unused' will lazy install only unused layers (i.e. layers
   ;; not listed in variable `dotspacemacs-configuration-layers'), `all' will
   ;; lazy install any layer that support lazy installation even the layers
   ;; listed in `dotspacemacs-configuration-layers'. `nil' disable the lazy
   ;; installation feature and you have to explicitly list a layer in the
   ;; variable `dotspacemacs-configuration-layers' to install it.
   ;; (default 'unused)
   dotspacemacs-enable-lazy-installation 'unused
   ;; If non-nil then Spacemacs will ask for confirmation before installing
   ;; a layer lazily. (default t)
   dotspacemacs-ask-for-lazy-installation t
   ;; If non-nil layers with lazy install support are lazy installed.
   ;; List of additional paths where to look for configuration layers.
   ;; Paths must have a trailing slash (i.e. `~/.mycontribs/')
   dotspacemacs-configuration-layer-path '()
   ;; List of configuration layers to load.
   dotspacemacs-configuration-layers
   '(
     csv
     javascript
     typescript
     html
     yaml
     rust
     python
     lsp
     ;; elpy
     csharp
     sql
     go
     ;; ----------------------------------------------------------------
     ;; Example of useful layers you may want to use right away.
     ;; Uncomment some layer names and press <SPC f e R> (Vim style) or
     ;; <M-m f e R> (Emacs style) to install them.
     ;; ----------------------------------------------------------------
     helm
     (auto-completion :variables
                      auto-completion-enable-snippets-in-popup t
                      auto-completion-enable-help-tooltip t)
     better-defaults
     emacs-lisp
     git
     markdown
     imenu-list
     (org :variables org-want-todo-bindings t)
     (shell :variables
            shell-default-height 20
            shell-default-position 'right)
     (spell-checking :variables
                     spell-checking-enable-by-default nil)
     syntax-checking
     version-control
     ;; notmuch
     ;; mu4e
     treemacs
     )
   ;; List of additional packages that will be installed without being
   ;; wrapped in a layer. If you need some configuration for these
   ;; packages, then consider creating a layer. You can also put the
   ;; configuration in `dotspacemacs/user-config'.
   dotspacemacs-additional-packages '(simpleclip
                                      flyspell-lazy
                                      github-theme
                                      solarized-theme
                                      doom-themes
                                      js-comint
                                      sr-speedbar
                                      all-the-icons
                                      imenu-anywhere)
   ;; A list of packages that cannot be updated.
   dotspacemacs-frozen-packages '()
   ;; A list of packages that will not be installed and loaded.
   dotspacemacs-excluded-packages '(org-projectile)
   ;; Defines the behaviour of Spacemacs when installing packages.
   ;; Possible values are `used-only', `used-but-keep-unused' and `all'.
   ;; `used-only' installs only explicitly used packages and uninstall any
   ;; unused packages as well as their unused dependencies.
   ;; `used-but-keep-unused' installs only the used packages but won't uninstall
   ;; them if they become unused. `all' installs *all* packages supported by
   ;; Spacemacs and never uninstall them. (default is `used-only')
   dotspacemacs-install-packages 'used-only)
 )

(defun dotspacemacs/init ()
  "Initialization function.
This function is called at the very startup of Spacemacs initialization
before layers configuration.
You should not put any user code in there besides modifying the variable
values."
  ;; This setq-default sexp is an exhaustive list of all the supported
  ;; spacemacs settings.
  (setq-default
   ;; If non nil ELPA repositories are contacted via HTTPS whenever it's
   ;; possible. Set it to nil if you have no way to use HTTPS in your
   ;; environment, otherwise it is strongly recommended to let it set to t.
   ;; This variable has no effect if Emacs is launched with the parameter
   ;; `--insecure' which forces the value of this variable to nil.
   ;; (default t)
   dotspacemacs-elpa-https t
   ;; Maximum allowed time in seconds to contact an ELPA repository.
   dotspacemacs-elpa-timeout 5
   ;; If non nil then spacemacs will check for updates at startup
   ;; when the current branch is not `develop'. Note that checking for
   ;; new versions works via git commands, thus it calls GitHub services
   ;; whenever you start Emacs. (default nil)
   dotspacemacs-check-for-update nil
   ;; If non-nil, a form that evaluates to a package directory. For example, to
   ;; use different package directories for different Emacs versions, set this
   ;; to `emacs-version'.
   dotspacemacs-elpa-subdirectory nil
   ;; One of `vim', `emacs' or `hybrid'.
   ;; `hybrid' is like `vim' except that `insert state' is replaced by the
   ;; `hybrid state' with `emacs' key bindings. The value can also be a list
   ;; with `:variables' keyword (similar to layers). Check the editing styles
   ;; section of the documentation for details on available variables.
   ;; (default 'vim)
   dotspacemacs-editing-style 'vim
   ;; If non nil output loading progress in `*Messages*' buffer. (default nil)
   dotspacemacs-verbose-loading nil
   ;; Specify the startup banner. Default value is `official', it displays
   ;; the official spacemacs logo. An integer value is the index of text
   ;; banner, `random' chooses a random text banner in `core/banners'
   ;; directory. A string value must be a path to an image format supported
   ;; by your Emacs build.
   ;; If the value is nil then no banner is displayed. (default 'official)
   dotspacemacs-startup-banner 'official
   ;; List of items to show in startup buffer or an association list of
   ;; the form `(list-type . list-size)`. If nil then it is disabled.
   ;; Possible values for list-type are:
   ;; `recents' `bookmarks' `projects' `agenda' `todos'."
   ;; List sizes may be nil, in which case
   ;; `spacemacs-buffer-startup-lists-length' takes effect.
   dotspacemacs-startup-lists '((recents . 5)
                                (projects . 7))
   ;; True if the home buffer should respond to resize events.
   dotspacemacs-startup-buffer-responsive t
   ;; Default major mode of the scratch buffer (default `text-mode')
   dotspacemacs-scratch-mode 'text-mode
   ;; List of themes, the first of the list is loaded when spacemacs starts.
   ;; Press <SPC> T n to cycle to the next theme in the list (works great
   ;; with 2 themes variants, one dark and one light)
   dotspacemacs-themes '(solarized-light
                         doom-one-light
                         doom-one
                         github
                         spacemacs-light
                         )

   ;; Set the theme for the Spaceline. Supported themes are `spacemacs',
   ;; `all-the-icons', `custom', `doom', `vim-powerline' and `vanilla'. The
   ;; first three are spaceline themes. `doom' is the doom-emacs mode-line.
   ;; `vanilla' is default Emacs mode-line. `custom' is a user defined themes,
   ;; refer to the DOCUMENTATION.org for more info on how to create your own
   ;; spaceline theme. Value can be a symbol or list with additional properties.
   ;; (default '(spacemacs :separator wave :separator-scale 1.5))
   dotspacemacs-mode-line-theme '(spacemacs :separator wave :separator-scale 1.0)

   ;; If non nil the cursor color matches the state color in GUI Emacs.
   dotspacemacs-colorize-cursor-according-to-state nil
   ;; Default font, or prioritized list of fonts. `powerline-scale' allows to
   ;; quickly tweak the mode-line size to make separators look not too crappy.
   dotspacemacs-default-font '("Iosevka Term"
                               :size 18
                               :weight normal
                               :width normal
                               :powerline-scale 1.1)
   ;; The leader key
   dotspacemacs-leader-key "SPC"
   ;; The key used for Emacs commands (M-x) (after pressing on the leader key).
   ;; (default "SPC")
   dotspacemacs-emacs-command-key "SPC"
   ;; The key used for Vim Ex commands (default ":")
   dotspacemacs-ex-command-key ":"
   ;; The leader key accessible in `emacs state' and `insert state'
   ;; (default "M-m")
   dotspacemacs-emacs-leader-key "M-m"
   ;; Major mode leader key is a shortcut key which is the equivalent of
   ;; pressing `<leader> m`. Set it to `nil` to disable it. (default ",")
   dotspacemacs-major-mode-leader-key ","
   ;; Major mode leader key accessible in `emacs state' and `insert state'.
   ;; (default "C-M-m")
   dotspacemacs-major-mode-emacs-leader-key "C-M-m"
   ;; These variables control whether separate commands are bound in the GUI to
   ;; the key pairs C-i, TAB and C-m, RET.
   ;; Setting it to a non-nil value, allows for separate commands under <C-i>
   ;; and TAB or <C-m> and RET.
   ;; In the terminal, these pairs are generally indistinguishable, so this only
   ;; works in the GUI. (default nil)
   dotspacemacs-distinguish-gui-tab t  ;; so C-i works for jump forward
   ;; If non nil `Y' is remapped to `y$' in Evil states. (default nil)
   dotspacemacs-remap-Y-to-y$ nil
   ;; If non-nil, the shift mappings `<' and `>' retain visual state if used
   ;; there. (default t)
   dotspacemacs-retain-visual-state-on-shift t
   ;; If non-nil, J and K move lines up and down when in visual mode.
   ;; (default nil)
   dotspacemacs-visual-line-move-text nil
   ;; If non nil, inverse the meaning of `g' in `:substitute' Evil ex-command.
   ;; (default nil)
   dotspacemacs-ex-substitute-global nil
   ;; Name of the default layout (default "Default")
   dotspacemacs-default-layout-name "Default"
   ;; If non nil the default layout name is displayed in the mode-line.
   ;; (default nil)
   dotspacemacs-display-default-layout nil
   ;; If non nil then the last auto saved layouts are resume automatically upon
   ;; start. (default nil)
   dotspacemacs-auto-resume-layouts t
   ;; Size (in MB) above which spacemacs will prompt to open the large file
   ;; literally to avoid performance issues. Opening a file literally means that
   ;; no major mode or minor modes are active. (default is 1)
   dotspacemacs-large-file-size 1
   ;; Location where to auto-save files. Possible values are `original' to
   ;; auto-save the file in-place, `cache' to auto-save the file to another
   ;; file stored in the cache directory and `nil' to disable auto-saving.
   ;; (default 'cache)
   dotspacemacs-auto-save-file-location 'cache
   ;; Maximum number of rollback slots to keep in the cache. (default 5)
   dotspacemacs-max-rollback-slots 5
   ;; If non nil, `helm' will try to minimize the space it uses. (default nil)
   dotspacemacs-helm-resize nil
   ;; if non nil, the helm header is hidden when there is only one source.
   ;; (default nil)
   dotspacemacs-helm-no-header nil
   ;; define the position to display `helm', options are `bottom', `top',
   ;; `left', or `right'. (default 'bottom)
   dotspacemacs-helm-position 'bottom
   ;; Controls fuzzy matching in helm. If set to `always', force fuzzy matching
   ;; in all non-asynchronous sources. If set to `source', preserve individual
   ;; source settings. Else, disable fuzzy matching in all sources.
   ;; (default 'always)
   dotspacemacs-helm-use-fuzzy 'always
   ;; If non nil the paste micro-state is enabled. When enabled pressing `p`
   ;; several times cycle between the kill ring content. (default nil)
   dotspacemacs-enable-paste-transient-state nil
   ;; Which-key delay in seconds. The which-key buffer is the popup listing
   ;; the commands bound to the current keystroke sequence. (default 0.4)
   dotspacemacs-which-key-delay 0.4
   ;; Which-key frame position. Possible values are `right', `bottom' and
   ;; `right-then-bottom'. right-then-bottom tries to display the frame to the
   ;; right; if there is insufficient space it displays it at the bottom.
   ;; (default 'bottom)
   dotspacemacs-which-key-position 'bottom
   ;; If non nil a progress bar is displayed when spacemacs is loading. This
   ;; may increase the boot time on some systems and emacs builds, set it to
   ;; nil to boost the loading time. (default t)
   dotspacemacs-loading-progress-bar t
   ;; If non nil the frame is fullscreen when Emacs starts up. (default nil)
   ;; (Emacs 24.4+ only)
   dotspacemacs-fullscreen-at-startup nil
   ;; If non nil `spacemacs/toggle-fullscreen' will not use native fullscreen.
   ;; Use to disable fullscreen animations in OSX. (default nil)
   dotspacemacs-fullscreen-use-non-native nil
   ;; If non nil the frame is maximized when Emacs starts up.
   ;; Takes effect only if `dotspacemacs-fullscreen-at-startup' is nil.
   ;; (default nil) (Emacs 24.4+ only)
   dotspacemacs-maximized-at-startup nil
   ;; A value from the range (0..100), in increasing opacity, which describes
   ;; the transparency level of a frame when it's active or selected.
   ;; Transparency can be toggled through `toggle-transparency'. (default 90)
   dotspacemacs-active-transparency 90
   ;; A value from the range (0..100), in increasing opacity, which describes
   ;; the transparency level of a frame when it's inactive or deselected.
   ;; Transparency can be toggled through `toggle-transparency'. (default 90)
   dotspacemacs-inactive-transparency 90
   ;; If non nil show the titles of transient states. (default t)
   dotspacemacs-show-transient-state-title t
   ;; If non nil show the color guide hint for transient state keys. (default t)
   dotspacemacs-show-transient-state-color-guide t
   ;; If non nil unicode symbols are displayed in the mode line. (default t)
   dotspacemacs-mode-line-unicode-symbols t
   ;; If non nil smooth scrolling (native-scrolling) is enabled. Smooth
   ;; scrolling overrides the default behavior of Emacs which recenters point
   ;; when it reaches the top or bottom of the screen. (default t)
   dotspacemacs-smooth-scrolling t
   ;; If non nil line numbers are turned on in all `prog-mode' and `text-mode'
   ;; derivatives. If set to `relative', also turns on relative line numbers.
   ;; (default nil)
   dotspacemacs-line-numbers t
   ;; Code folding method. Possible values are `evil' and `origami'.
   ;; (default 'evil)
   dotspacemacs-folding-method 'evil
   ;; If non-nil smartparens-strict-mode will be enabled in programming modes.
   ;; (default nil)
   dotspacemacs-smartparens-strict-mode nil
   ;; If non-nil pressing the closing parenthesis `)' key in insert mode passes
   ;; over any automatically added closing parenthesis, bracket, quote, etc…
   ;; This can be temporary disabled by pressing `C-q' before `)'. (default nil)
   dotspacemacs-smart-closing-parenthesis nil
   ;; Select a scope to highlight delimiters. Possible values are `any',
   ;; `current', `all' or `nil'. Default is `all' (highlight any scope and
   ;; emphasis the current one). (default 'all)
   dotspacemacs-highlight-delimiters 'all
   ;; If non nil, advise quit functions to keep server open when quitting.
   ;; (default nil)
   dotspacemacs-persistent-server nil
   ;; List of search tool executable names. Spacemacs uses the first installed
   ;; tool of the list. Supported tools are `ag', `pt', `ack' and `grep'.
   ;; (default '("ag" "pt" "ack" "grep"))
   dotspacemacs-search-tools '("ag" "pt" "ack" "grep")
   ;; The default package repository used if no explicit repository has been
   ;; specified with an installed package.
   ;; Not used for now. (default nil)
   dotspacemacs-default-package-repository nil
   ;; Delete whitespace while saving buffer. Possible values are `all'
   ;; to aggressively delete empty line and long sequences of whitespace,
   ;; `trailing' to delete only the whitespace at end of lines, `changed'to
   ;; delete only whitespace for changed lines or `nil' to disable cleanup.
   ;; (default nil)
   dotspacemacs-whitespace-cleanup nil
   ))

(defun dotspacemacs/user-init ()
  "Initialization function for user code.
It is called immediately after `dotspacemacs/init', before layer configuration
executes.
 This function is mostly useful for variables that need to be set
before packages are loaded. If you are unsure, you should try in setting them in
`dotspacemacs/user-config' first."
    ;; For python
    (add-hook 'python-mode-hook #'(lambda () (modify-syntax-entry ?_ "w")))
    ;; For ruby
    (add-hook 'ruby-mode-hook #'(lambda () (modify-syntax-entry ?_ "w")))
    ;; For Javascript
    (add-hook 'js2-mode-hook #'(lambda () (modify-syntax-entry ?_ "w")))
    ;(add-hook 'persp-activated-functions #'(lambda (p) (spacemacs//pyenv-mode-set-local-version)))

    ; dont auto set pyvenv, slow load
    (setq python-auto-set-local-pyvenv-virtualenv nil)
    (setq python-auto-set-local-pyenv-version nil)
  )

(defun dotspacemacs/user-config ()
  "Configuration function for user code.
This function is called at the very end of Spacemacs initialization after
layers configuration.
This is the place where most of your configurations should be done. Unless it is
explicitly specified that a variable should be set before a package is loaded,
you should place your code here."

    (require 'helm-bookmark)

    (global-linum-mode)
    (global-company-mode t)

    ;; window control bindings for special buffers
    (with-eval-after-load 'neotree
      (define-key neotree-mode-map (kbd "C-w l") 'evil-window-right)
      (define-key neotree-mode-map (kbd "C-w C-w") 'evil-window-next)
      (define-key neotree-mode-map (kbd "C-w q") 'delete-window))
    (with-eval-after-load 'imenu-list
      (define-key imenu-list-major-mode-map (kbd "C-w h") 'evil-window-left)
      (define-key imenu-list-major-mode-map (kbd "C-w C-w") 'evil-window-next)
      (define-key imenu-list-major-mode-map (kbd "C-w q") 'delete-window))
    (with-eval-after-load 'imenu-anywhere
      (spacemacs/set-leader-keys "jI" #'imenu-anywhere))

    (with-eval-after-load 'company
      (define-key company-active-map (kbd "C-w") 'evil-delete-backward-word)
      (define-key company-active-map (kbd "C-k") 'company-select-previous)
      )
    (with-eval-after-load 'helm
      (define-key helm-map (kbd "C-w") 'evil-delete-backward-word)
      )
    (remove-hook 'prog-mode-hook #'smartparens-mode)
    (spacemacs/toggle-smartparens-globally-off)
    (define-key evil-window-map "q" 'delete-window)

    (setq-default frame-title-format "Spacemacs - %b (%f)")

  ;;; scroll one line at a time (less "jumpy" than defaults)
    (setq mouse-wheel-scroll-amount '(2 ((shift) . 1))) ;; two lines at a time
    (setq mouse-wheel-progressive-speed nil) ;; don't accelerate scrolling
    (setq mouse-wheel-follow-mouse 't) ;; scroll window under mouse
    (setq scroll-preserve-screen-position 't)
    (setq scroll-margin 5)

    ;; clipboard preferences
    (simpleclip-mode 1)

    ;; ORG MODE CONFIG
    (setq org-want-todo-bindings t)
    (setq org-agenda-files '("~/Dropbox/org/TODOs.org" "~/Dropbox/org/projects.org" "~/Dropbox/org/notes.org" "~/Dropbox/org/meetings.org"))
    (setq org-todo-keywords
          (quote ((sequence "TODO(t)" "NEXT(n)" "|" "DONE(d)")
                  (sequence "WAITING(w@/!)" "HOLD(h@/!)" "|" "CANCELLED(c@/!)" "PHONE" "MEETING"))))

    (setq org-todo-keyword-faces
          (quote (("TODO" :foreground "red" :weight bold)
                  ("NEXT" :foreground "blue" :weight bold)
                  ("DONE" :foreground "forest green" :weight bold)
                  ("WAITING" :foreground "orange" :weight bold)
                  ("HOLD" :foreground "magenta" :weight bold)
                  ("CANCELLED" :foreground "forest green" :weight bold)
                  ("MEETING" :foreground "forest green" :weight bold)
                  ("PHONE" :foreground "forest green" :weight bold))))
    (setq org-directory "~/Dropbox/org")
    (setq org-default-notes-file "~/Dropbox/org/TODOs.org")
    (setq org-clock-idle-time 10)

    ;; Capture templates for: TODO tasks, Notes, appointments, phone calls, meetings, and org-protocol
    (setq org-capture-templates
          (quote (("i" "inbox" entry (file+headline "~/Dropbox/org/TODOs.org" "INBOX")
                  "* TODO %?\n:PROPERTIES:\n:CREATED: %U\n:END:\n" :prepend t)
                  ("n" "note" entry (file+headline "~/Dropbox/org/TODOs.org" "INBOX")
                  "* %? :NOTE:\n%U\n")
                  ("m" "Meeting" entry (file+headline "~/Dropbox/org/TODOs.org" "INBOX")
                  "* MEETING on %U with %? :MEETING:\n:PROPERTIES:\n:CREATED: %U\n:END:\n"))))
    (setq org-agenda-custom-commands
      '(("n" todo "NEXT")))
    (setq org-refile-targets '((nil :maxlevel . 9)
                                (org-agenda-files :maxlevel . 9)))
    (setq org-outline-path-complete-in-steps nil)         ; Refile in a single go
    (setq org-refile-use-outline-path t)                  ; Show full paths for refiling
    (global-set-key (kbd "<f12>") 'org-agenda)
    (setq org-mu4e-link-query-in-headers-mode nil)

    (advice-add 'org-refile :after
        (lambda (&rest _)
        (org-save-all-org-buffers)))
    (advice-add 'org-archive-subtree :after
        (lambda (&rest _)
          (org-save-all-org-buffers)))
    ;; END ORG MODE

    ;; persp keybindings
    (define-key winum-keymap "\M-0" 'spacemacs/persp-switch-to-0)
    (define-key winum-keymap "\M-1" 'spacemacs/persp-switch-to-1)
    (define-key winum-keymap "\M-2" 'spacemacs/persp-switch-to-2)
    (define-key winum-keymap "\M-3" 'spacemacs/persp-switch-to-3)
    (define-key winum-keymap "\M-4" 'spacemacs/persp-switch-to-4)
    (define-key winum-keymap "\M-5" 'spacemacs/persp-switch-to-5)
    (define-key winum-keymap "\M-6" 'spacemacs/persp-switch-to-6)
    (define-key winum-keymap "\M-7" 'spacemacs/persp-switch-to-7)
    (define-key winum-keymap "\M-8" 'spacemacs/persp-switch-to-8)
    (define-key winum-keymap "\M-9" 'spacemacs/persp-switch-to-9)

    ;; display which function we're in
    (which-function-mode)

    ;; find other file
    (with-eval-after-load 'projectile
      (push '("html" "js") projectile-other-file-alist) ;; switch from html -> js
      (push '("js" "html") projectile-other-file-alist) ;; switch from js -> html
      (push '("component.js" "component.html" "state.js") projectile-other-file-alist)
      (push '("component.html" "component.js" "state.js") projectile-other-file-alist)
      (push '("state.js" "state.spec.js" "component.js" "component.html") projectile-other-file-alist)
      (push '("state.spec.js" "state.js") projectile-other-file-alist)
     )

    (setq projectile-use-git-grep 1)

    ;; lazy spellcheck
    (flyspell-lazy-mode 1)

    ; JS
    (setq-default js2-basic-offset 4)
    (with-eval-after-load 'js2-mode
      (load (expand-file-name "private/init-javascript.el" user-emacs-directory)))

    ; switch buffers
    (global-set-key (kbd "C-l") 'next-buffer)
    (global-set-key (kbd "C-h") 'previous-buffer)
    (global-set-key (kbd "C-\\") 'neotree-find-project-root)

    ; neotree hidden
    (setq neo-hidden-regexp-list '("^\\." "\\.cs\\.meta$" "\\.pyc$" "~$" "^#.*#$" "\\.elc$" "__pycache__"))
    (setq projectile-switch-project-action 'neotree-projectile-action)
    (setq neo-theme 'classic)

    ; theme customization
    (setq solarized-use-more-italic t)
    (setq solarized-high-contrast-mode-line nil)

    ;; ; flycheck custom
    ;; (setq flycheck-check-syntax-automatically '(idle-change))


    ; Emacs as an Org capture server
    ; https://gist.github.com/progfolio/af627354f87542879de3ddc30a31adc1
    (defun my/delete-capture-frame (&rest _)
      "Delete frame with its name frame-parameter set to \"capture\"."
      (if (equal "capture" (frame-parameter nil 'name))
          (delete-frame)))

    (advice-add 'org-capture-finalize :after #'my/delete-capture-frame)

    (defun my/org-capture-frame ()
      "Run org-capture in its own frame."
      (interactive)
      (require 'cl-lib)
      (select-frame-by-name "capture")
      (delete-other-windows)
      (cl-letf (((symbol-function 'switch-to-buffer-other-window) #'switch-to-buffer))
        (condition-case err
            (org-capture)
          ;; "q" signals (error "Abort") in `org-capture'
          ;; delete the newly created frame in this scenario.
          (user-error (when (string= (cadr err) "Abort")
                        (delete-frame))))))
)
(custom-set-variables
 ;; custom-set-variables was added by Custom.
 ;; If you edit it by hand, you could mess it up, so be careful.
 ;; Your init file should contain only one such instance.
 ;; If there is more than one, they won't work right.
 '(package-selected-packages
   (quote
    (log4e gntp skewer-mode json-snatcher json-reformat lv parent-mode request haml-mode fringe-helper git-gutter+ git-gutter pkg-info flx transient diminish web-completion-data tern pos-tip go-mode bind-map memoize helm auto-complete popup imenu-anywhere typescript-mode powerline alert org-plus-contrib multiple-cursors hydra projectile csharp-mode rust-mode bind-key packed anaconda-mode all-the-icons dash-functional company iedit smartparens highlight evil goto-chg flycheck epl flyspell-correct yasnippet gitignore-mode helm-core avy magit magit-popup git-commit ghub with-editor async markdown-mode pythonic f js2-mode simple-httpd s org-mime yapfify yaml-mode xterm-color ws-butler winum which-key web-mode web-beautify volatile-highlights vi-tilde-fringe uuidgen use-package unfill toml-mode toc-org tide tagedit sr-speedbar sql-indent spaceline solarized-theme smeargle slim-mode simpleclip shell-pop scss-mode sass-mode restart-emacs rainbow-delimiters racer pyvenv pytest pyenv-mode py-isort pug-mode popwin pip-requirements persp-mode pcre2el paradox orgit org-present org-pomodoro org-download org-bullets open-junk-file omnisharp neotree mwim multi-term move-text mmm-mode markdown-toc magit-gitflow macrostep lorem-ipsum livid-mode live-py-mode linum-relative link-hint less-css-mode json-mode js2-refactor js-doc js-comint indent-guide imenu-list hy-mode hungry-delete htmlize hl-todo highlight-parentheses highlight-numbers highlight-indentation helm-themes helm-swoop helm-pydoc helm-projectile helm-mode-manager helm-make helm-gitignore helm-flx helm-descbinds helm-css-scss helm-company helm-c-yasnippet helm-ag google-translate golden-ratio go-guru go-eldoc gnuplot github-theme gitconfig-mode gitattributes-mode git-timemachine git-messenger git-link git-gutter-fringe git-gutter-fringe+ gh-md fuzzy flyspell-lazy flyspell-correct-helm flycheck-rust flycheck-pos-tip flx-ido fill-column-indicator fancy-battery eyebrowse expand-region exec-path-from-shell evil-visualstar evil-visual-mark-mode evil-unimpaired evil-tutor evil-surround evil-search-highlight-persist evil-numbers evil-nerd-commenter evil-mc evil-matchit evil-magit evil-lisp-state evil-indent-plus evil-iedit-state evil-exchange evil-escape evil-ediff evil-args evil-anzu eval-sexp-fu eshell-z eshell-prompt-extras esh-help emmet-mode elisp-slime-nav dumb-jump doom-themes diff-hl define-word cython-mode csv-mode company-web company-tern company-statistics company-quickhelp company-go company-anaconda column-enforce-mode coffee-mode clean-aindent-mode cargo auto-yasnippet auto-highlight-symbol auto-dictionary auto-compile aggressive-indent adaptive-wrap ace-window ace-link ace-jump-helm-line ac-ispell))))
(custom-set-faces
 ;; custom-set-faces was added by Custom.
 ;; If you edit it by hand, you could mess it up, so be careful.
 ;; Your init file should contain only one such instance.
 ;; If there is more than one, they won't work right.
 )
(defun dotspacemacs/emacs-custom-settings ()
  "Emacs custom settings.
This is an auto-generated function, do not modify its content directly, use
Emacs customize menu instead.
This function is called at the very end of Spacemacs initialization."
(custom-set-variables
 ;; custom-set-variables was added by Custom.
 ;; If you edit it by hand, you could mess it up, so be careful.
 ;; Your init file should contain only one such instance.
 ;; If there is more than one, they won't work right.
 '(package-selected-packages
   (quote
    (lsp-ui lsp-treemacs lsp-python-ms helm-lsp company-lsp lsp-mode log4e gntp skewer-mode json-snatcher json-reformat lv parent-mode request haml-mode fringe-helper git-gutter+ git-gutter pkg-info flx transient diminish web-completion-data tern pos-tip go-mode bind-map memoize helm auto-complete popup imenu-anywhere typescript-mode powerline alert org-plus-contrib multiple-cursors hydra projectile csharp-mode rust-mode bind-key packed anaconda-mode all-the-icons dash-functional company iedit smartparens highlight evil goto-chg flycheck epl flyspell-correct yasnippet gitignore-mode helm-core avy magit magit-popup git-commit ghub with-editor async markdown-mode pythonic f js2-mode simple-httpd s org-mime yapfify yaml-mode xterm-color ws-butler winum which-key web-mode web-beautify volatile-highlights vi-tilde-fringe uuidgen use-package unfill toml-mode toc-org tide tagedit sr-speedbar sql-indent spaceline solarized-theme smeargle slim-mode simpleclip shell-pop scss-mode sass-mode restart-emacs rainbow-delimiters racer pyvenv pytest pyenv-mode py-isort pug-mode popwin pip-requirements persp-mode pcre2el paradox orgit org-present org-pomodoro org-download org-bullets open-junk-file omnisharp neotree mwim multi-term move-text mmm-mode markdown-toc magit-gitflow macrostep lorem-ipsum livid-mode live-py-mode linum-relative link-hint less-css-mode json-mode js2-refactor js-doc js-comint indent-guide imenu-list hy-mode hungry-delete htmlize hl-todo highlight-parentheses highlight-numbers highlight-indentation helm-themes helm-swoop helm-pydoc helm-projectile helm-mode-manager helm-make helm-gitignore helm-flx helm-descbinds helm-css-scss helm-company helm-c-yasnippet helm-ag google-translate golden-ratio go-guru go-eldoc gnuplot github-theme gitconfig-mode gitattributes-mode git-timemachine git-messenger git-link git-gutter-fringe git-gutter-fringe+ gh-md fuzzy flyspell-lazy flyspell-correct-helm flycheck-rust flycheck-pos-tip flx-ido fill-column-indicator fancy-battery eyebrowse expand-region exec-path-from-shell evil-visualstar evil-visual-mark-mode evil-unimpaired evil-tutor evil-surround evil-search-highlight-persist evil-numbers evil-nerd-commenter evil-mc evil-matchit evil-magit evil-lisp-state evil-indent-plus evil-iedit-state evil-exchange evil-escape evil-ediff evil-args evil-anzu eval-sexp-fu eshell-z eshell-prompt-extras esh-help emmet-mode elisp-slime-nav dumb-jump doom-themes diff-hl define-word cython-mode csv-mode company-web company-tern company-statistics company-quickhelp company-go company-anaconda column-enforce-mode coffee-mode clean-aindent-mode cargo auto-yasnippet auto-highlight-symbol auto-dictionary auto-compile aggressive-indent adaptive-wrap ace-window ace-link ace-jump-helm-line ac-ispell))))
(custom-set-faces
 ;; custom-set-faces was added by Custom.
 ;; If you edit it by hand, you could mess it up, so be careful.
 ;; Your init file should contain only one such instance.
 ;; If there is more than one, they won't work right.
 '(default ((((class color) (min-colors 89)) (:foreground "#657b83" :background "#fdf6e3")))))
)
