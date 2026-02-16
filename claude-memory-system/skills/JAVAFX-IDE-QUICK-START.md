# JavaFX IDE Designer - Quick Start Guide

## Overview

**Complete skill for designing IDE (Integrated Development Environment) interfaces using JavaFX.**

**Size:** 1,409 lines (38KB)
**Skill File:** `javafx-ide-designer.md`

---

## What This Skill Provides

### 🎨 Complete IDE Layout

```
┌─────────────────────────────────────────────────────────┐
│  Menu Bar (File | Edit | View | Run | Help)            │
├─────────────────────────────────────────────────────────┤
│  Tool Bar (New, Open, Save, Cut, Copy, Run, etc.)      │
├──────────┬──────────────────────────────────────────────┤
│          │                                              │
│  File    │      Code Editor (Tabs)                     │
│  Tree    │      - Syntax highlighting                  │
│          │      - Line numbers                          │
│  [Proj]  │      - Multiple tabs                         │
│  ├─src   │      - Auto-complete ready                   │
│  │ └─..  │                                              │
│  └─test  │                                              │
│          ├──────────────────────────────────────────────┤
│          │  Console / Terminal / Problems              │
│          │  [Output] [Terminal] [Problems]             │
├──────────┴──────────────────────────────────────────────┤
│  Status Bar: file.java | Ln 42, Col 15 | UTF-8 | Java │
└─────────────────────────────────────────────────────────┘
```

---

## Key Components Included

### ✅ 1. Menu Bar Component
- File menu (New, Open, Save, Exit)
- Edit menu (Undo, Redo, Cut, Copy, Paste, Find, Replace)
- View menu (Toggle panels)
- Run menu (Run, Debug, Stop)
- Help menu (Documentation, About)
- **Keyboard shortcuts included!**

### ✅ 2. Tool Bar Component
- Icon buttons for common actions
- Search field
- Theme toggle
- Using FontAwesome icons

### ✅ 3. File Tree Component
- Lazy-loading directory tree
- File/folder icons
- Context menu (New, Delete, Rename)
- Drag & drop ready

### ✅ 4. Code Editor (RichTextFX)
- **Syntax highlighting** (Java by default)
- **Line numbers**
- Multiple tabs
- Tab key = 4 spaces
- Extensible for other languages

### ✅ 5. Console Component
- Output tab (program output)
- Terminal tab (command execution)
- Problems tab (errors/warnings table)
- Clear button

### ✅ 6. Status Bar
- Current file name
- Cursor position (line, column)
- File encoding
- Language mode
- Status messages

### ✅ 7. Dark Theme CSS
- Complete VS Code-like dark theme
- Syntax highlighting colors
- All controls themed
- Professional look

---

## Maven Dependencies Required

```xml
<dependencies>
    <!-- JavaFX 21 -->
    <dependency>
        <groupId>org.openjfx</groupId>
        <artifactId>javafx-controls</artifactId>
        <version>21.0.1</version>
    </dependency>

    <!-- RichTextFX (Code Editor) -->
    <dependency>
        <groupId>org.fxmisc.richtext</groupId>
        <artifactId>richtextfx</artifactId>
        <version>0.11.2</version>
    </dependency>

    <!-- ControlsFX (Extra Controls) -->
    <dependency>
        <groupId>org.controlsfx</groupId>
        <artifactId>controlsfx</artifactId>
        <version>11.2.0</version>
    </dependency>

    <!-- FontAwesomeFX (Icons) -->
    <dependency>
        <groupId>de.jensd</groupId>
        <artifactId>fontawesomefx-fontawesome</artifactId>
        <version>4.7.0-9.1.2</version>
    </dependency>
</dependencies>
```

---

## Quick Start Usage

### Step 1: Create Main Application

```java
public class IDEApplication extends Application {
    @Override
    public void start(Stage primaryStage) {
        MainWindow mainWindow = new MainWindow();
        Scene scene = new Scene(mainWindow, 1400, 900);

        // Load dark theme
        scene.getStylesheets().add(
            getClass().getResource("/styles/dark-theme.css").toExternalForm()
        );

        primaryStage.setScene(scene);
        primaryStage.setTitle("MyIDE");
        primaryStage.show();
    }
}
```

### Step 2: Use Provided Components

```java
public class MainWindow extends BorderPane {
    public MainWindow() {
        // Top: Menu + Toolbar
        setTop(new VBox(
            new MenuBarComponent(),
            new ToolBarComponent()
        ));

        // Center: File Tree + Editor + Console
        SplitPane mainSplit = new SplitPane(
            new FileTreeComponent(),
            new SplitPane(
                new EditorTabPaneComponent(),
                new ConsoleComponent()
            )
        );
        setCenter(mainSplit);

        // Bottom: Status Bar
        setBottom(new StatusBarComponent());
    }
}
```

---

## Syntax Highlighting

### Java Keywords Highlighted:

```
Keywords:   abstract, class, if, for, while, etc.
Strings:    "hello world"
Comments:   // single line
            /* multi line */
Braces:     { } ( ) [ ]
```

**Colors (Dark Theme):**
- Keywords: Blue (`#569cd6`)
- Strings: Orange (`#ce9178`)
- Comments: Green (`#6a9955`)
- Brackets: Gold (`#ffd700`)

### Extensible to Other Languages:

Modify `computeHighlighting()` method to add:
- Python syntax
- JavaScript syntax
- C/C++ syntax
- etc.

---

## Context7 Integration

**MANDATORY before implementation:**

```java
// Always query Context7 first!
context7.search("JavaFX 21 latest documentation 2026");
context7.search("RichTextFX syntax highlighting latest");
context7.search("JavaFX dark theme CSS best practices");
```

**Why Critical:**
- JavaFX versions update (21, 22, etc.)
- RichTextFX API changes
- Performance optimizations evolve
- CSS properties update

---

## Keyboard Shortcuts Included

| Action | Shortcut |
|--------|----------|
| New File | Ctrl+N |
| Open File | Ctrl+O |
| Save | Ctrl+S |
| Save As | Ctrl+Shift+S |
| Exit | Ctrl+Q |
| Undo | Ctrl+Z |
| Redo | Ctrl+Y |
| Cut | Ctrl+X |
| Copy | Ctrl+C |
| Paste | Ctrl+V |
| Find | Ctrl+F |
| Replace | Ctrl+H |
| Run | F5 |
| Debug | F9 |
| Stop | F6 |

---

## File Structure

```
src/
├── main/
│   ├── java/
│   │   └── com/yourapp/
│   │       ├── IDEApplication.java
│   │       └── ui/
│   │           ├── MainWindow.java
│   │           └── components/
│   │               ├── MenuBarComponent.java
│   │               ├── ToolBarComponent.java
│   │               ├── FileTreeComponent.java
│   │               ├── EditorTabPaneComponent.java
│   │               ├── ConsoleComponent.java
│   │               └── StatusBarComponent.java
│   └── resources/
│       └── styles/
│           └── dark-theme.css
└── module-info.java
```

---

## Features Comparison

### ✅ Included (Production Ready):

- [x] Menu Bar with all menus
- [x] Tool Bar with icons
- [x] File Tree with lazy loading
- [x] Multi-tab code editor
- [x] Syntax highlighting (Java)
- [x] Line numbers
- [x] Console with tabs
- [x] Status bar
- [x] Dark theme CSS
- [x] Resizable split panes
- [x] Context menus
- [x] Keyboard shortcuts

### 🚧 Can Be Extended:

- [ ] Autocomplete (integrate with IDE frameworks)
- [ ] Debugger UI
- [ ] Git integration UI
- [ ] Plugin system
- [ ] Settings dialog
- [ ] Find & Replace dialog
- [ ] Multiple color themes
- [ ] Minimap
- [ ] Breadcrumbs

---

## Customization Examples

### Change Syntax Highlighting Language:

```java
// Add Python highlighting
private StyleSpans<Collection<String>> computePythonHighlighting(String text) {
    String[] KEYWORDS = {"def", "class", "if", "for", "import", "return", ...};
    // Similar pattern to Java highlighting
}
```

### Change Theme:

```css
/* light-theme.css */
.root {
    -fx-base: #ffffff;
    -fx-background: #f3f3f3;
    -fx-text-fill: #000000;
}
/* ... rest of theme */
```

### Add More File Types:

```java
private ImageView getFileIcon(File file) {
    String name = file.getName().toLowerCase();
    if (name.endsWith(".java")) return javaIcon;
    if (name.endsWith(".py")) return pythonIcon;
    if (name.endsWith(".js")) return jsIcon;
    // ... etc.
}
```

---

## Performance Tips

### For Large Files:

```java
// Lazy load file content
codeArea.setUseInitialStyleForInsertion(true);

// Virtual flow for long files
codeArea.setWrapText(false);

// Syntax highlight on demand
codeArea.richChanges()
    .successionEnds(Duration.ofMillis(500))  // Debounce
    .subscribe(change -> updateSyntax());
```

### For Large Projects:

```java
// Virtual TreeView
treeView.setFixedCellSize(24);

// Lazy expand directories
item.expandedProperty().addListener((obs, was, is) -> {
    if (is) loadChildren(item);
});
```

---

## Common Issues & Solutions

### Issue: JavaFX not found

**Solution:**
```xml
<!-- Add to pom.xml -->
<plugin>
    <groupId>org.openjfx</groupId>
    <artifactId>javafx-maven-plugin</artifactId>
    <version>0.0.8</version>
</plugin>
```

Run: `mvn javafx:run`

### Issue: CSS not applied

**Solution:**
```java
// Use correct path
scene.getStylesheets().add(
    getClass().getResource("/styles/dark-theme.css").toExternalForm()
);

// Ensure file is in resources folder
// src/main/resources/styles/dark-theme.css
```

### Issue: Icons not showing

**Solution:**
```xml
<!-- Add FontAwesome dependency -->
<dependency>
    <groupId>de.jensd</groupId>
    <artifactId>fontawesomefx-fontawesome</artifactId>
    <version>4.7.0-9.1.2</version>
</dependency>
```

---

## Real-World Usage Examples

### Example 1: Simple Text Editor

```java
// Minimal version - just editor
EditorTabPaneComponent editor = new EditorTabPaneComponent();
Scene scene = new Scene(editor, 800, 600);
```

### Example 2: Code Viewer

```java
// Read-only with syntax highlighting
CodeArea viewer = new CodeArea();
viewer.setEditable(false);
viewer.replaceText(sourceCode);
viewer.setStyleSpans(0, computeHighlighting(sourceCode));
```

### Example 3: Full IDE

```java
// Complete layout (as shown in skill)
MainWindow mainWindow = new MainWindow();
// Includes all components
```

---

## When to Use This Skill

✅ Building an IDE
✅ Creating code editor
✅ Text editor with syntax highlighting
✅ File manager with code preview
✅ Log viewer with highlighting
✅ Configuration editor
✅ JavaFX desktop application with editor

---

## Integration with Other Tools

### Can Integrate With:

1. **Compiler APIs** (Java Compiler API)
2. **Git libraries** (JGit)
3. **Language Servers** (LSP4J)
4. **Build tools** (Maven, Gradle)
5. **Debuggers** (JPDA)

### Example: Compile Code

```java
JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
DiagnosticCollector<JavaFileObject> diagnostics = new DiagnosticCollector<>();
compiler.getTask(null, fileManager, diagnostics, null, null, files).call();

// Show errors in Problems tab
for (Diagnostic diagnostic : diagnostics.getDiagnostics()) {
    problemsTable.getItems().add(new Problem(
        diagnostic.getKind().toString(),
        diagnostic.getMessage(null),
        diagnostic.getSource().getName(),
        (int) diagnostic.getLineNumber()
    ));
}
```

---

## Quick Reference

**File:** `javafx-ide-designer.md`
**Size:** 1,409 lines (38KB)
**Components:** 7 major components
**Theme:** Dark theme CSS included
**Ready:** Production-ready IDE layout

**Key Libraries:**
- JavaFX 21+
- RichTextFX 0.11+
- ControlsFX 11+
- FontAwesomeFX 4.7+

**Context7:** Mandatory for latest APIs

---

## Next Steps After Using Skill

1. ✅ Copy component code
2. ✅ Add Maven dependencies
3. ✅ Create resources folder
4. ✅ Add dark-theme.css
5. ✅ Run application
6. ✅ Customize as needed

---

**Complete IDE design capability in JavaFX! 🚀🎨**
