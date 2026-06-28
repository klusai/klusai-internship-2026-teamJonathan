The filesystem MCP server exposes these 14 tools:

┌────────────────────────────────────────────┬──────────────────────────────────────────────┐             
│                    Tool                    │                   Purpose                    │             
├────────────────────────────────────────────┼──────────────────────────────────────────────┤             
│ mcp__filesystem__read_file                 │ Read a file's contents                       │             
├────────────────────────────────────────────┼──────────────────────────────────────────────┤             
│ mcp__filesystem__read_text_file            │ Read a file as text                          │             
├────────────────────────────────────────────┼──────────────────────────────────────────────┤             
│ mcp__filesystem__read_media_file           │ Read an image/media file                     │             
├────────────────────────────────────────────┼──────────────────────────────────────────────┤             
│ mcp__filesystem__read_multiple_files       │ Read several files at once                   │             
├────────────────────────────────────────────┼──────────────────────────────────────────────┤             
│ mcp__filesystem__write_file                │ Create or overwrite a file                   │             
├────────────────────────────────────────────┼──────────────────────────────────────────────┤             
│ mcp__filesystem__edit_file                 │ Make line-based edits to a file              │             
├────────────────────────────────────────────┼──────────────────────────────────────────────┤             
│ mcp__filesystem__create_directory          │ Create a directory                           │             
├────────────────────────────────────────────┼──────────────────────────────────────────────┤             
│ mcp__filesystem__list_directory            │ List entries in a directory                  │             
├────────────────────────────────────────────┼──────────────────────────────────────────────┤             
│ mcp__filesystem__list_directory_with_sizes │ List entries with file sizes                 │             
├────────────────────────────────────────────┼──────────────────────────────────────────────┤             
│ mcp__filesystem__directory_tree            │ Recursive tree view of a directory           │             
├────────────────────────────────────────────┼──────────────────────────────────────────────┤             
│ mcp__filesystem__move_file                 │ Move or rename a file/directory              │             
├────────────────────────────────────────────┼──────────────────────────────────────────────┤             
│ mcp__filesystem__search_files              │ Search for files by pattern                  │             
├────────────────────────────────────────────┼──────────────────────────────────────────────┤             
│ mcp__filesystem__get_file_info             │ Get metadata for a file/directory            │             
├────────────────────────────────────────────┼──────────────────────────────────────────────┤             
│ mcp__filesystem__list_allowed_directories  │ Show which directories the server may access │             
└────────────────────────────────────────────┴──────────────────────────────────────────────┘

These come from the deferred-tools list in this session. Note their schemas aren't loaded yet — if you    
want me to actually call one (e.g. check which directories it's allowed to access), I'd load its schema   
first via ToolSearch and then run it. Want me to do that?                                       