import sublime
import sublime_plugin
import os
import collections
import re


START_TEXT = 'BEGIN SNIPLATE'
END_TEXT = 'END SNIPLATE'

line_comments = {'cpp': '//', 'py': '#'}

context = {}

'''
特定の言語にしかまだ対応していない
pattern: 独自のものを使用
require: OK
invisible: OK
class: OK
abbr: OK
var: OK
priority: OK
cursor: 未対応
'''


class SniplateLang:
    def __init__(self, lang, last):
        self.lang = lang
        self.last = last
        self.sniplates = {}
        self.sniplate_list = []
        self.candidate_list = []

    def build(self, sniplates):
        sniplates_dict = {s.name: s for s in sniplates}

        # 重複チェック
        if len(sniplates_dict) != len(sniplates):
            cntr = collections.Counter(s.name for s in sniplates)
            error_message = []
            for c in cntr:
                if cntr[c] > 1:
                    error_message.append('Sniplate `{0}` has been declared more than once'.format(c))
            sublime.error_message('\n'.join(error_message))
            return False

        # 依存関係をトポロジカルソートしてループが無いかを調べる
        used = set()
        indeg = collections.defaultdict(int)
        for s in sniplates:
            for req in s.requires:
                indeg[req] += 1

        q = collections.deque()
        for s in sniplates:
            if indeg[s.name] == 0 and s.name not in used:
                q.append(s.name)
                used.add(s.name)
                while q:
                    cur = q.popleft()
                    for nex in sniplates_dict[cur].requires:
                        indeg[nex] -= 1
                        if indeg[nex] == 0 and nex not in used:
                            used.add(nex)
                            q.append(nex)

        if max(indeg.values()) != 0:
            # ループがあった
            error_message = 'A loop appear in dependency graph'
            sublime.error_message(error_message)
            return False
        self.sniplates = sniplates_dict

        self.sniplate_list = [s for s in sniplates if not s.invisible]
        self.sniplate_list.sort(key=lambda s: (-s.priority, s.name))
        self.candidate_list = [[s.name, s.abbr + ' ' + str(s.classes)] for s in self.sniplate_list]

        return True


class Sniplate:
    def __init__(self, name, filename, line_comment, lines):
        self.name = name
        self.filename = filename
        self.lines = lines
        self.requires = []
        self.classes = []
        self.abbr = ''
        self.pattern_line = ' '.join([line_comment, 'sniplate:', self.name])

        self.invisible = False
        self.priority = 0

    def __repr__(self):
        return '<Sniplate {0}>'.format(self.name)

    def command(self, name, arg):
        if name == 'invisible':
            self.invisible = True
        elif name == 'require':
            if arg:
                self.requires.extend(a.strip() for a in arg.split(','))
        elif name == 'class':
            if arg:
                self.classes.append(arg)
        elif name == 'abbr':
            if arg:
                self.abbr = arg
        elif name == 'priority':
            if arg:
                self.priority = int(arg)


def read_sniplates(fn, line_comment):
    sniplates = []
    with open(fn) as f:
        name = None
        commands = []
        lines = []

        def new():
            sniplate = Sniplate(name, fn, line_comment, lines)
            for c in commands:
                sniplate.command(*c)
            sniplates.append(sniplate)

        for l in f:
            l = l.rstrip('\r\n')
            striped = l.strip()

            if striped.startswith(line_comment):
                # コメント行

                idx = l.find(START_TEXT)
                if idx >= 0:
                    # start
                    if name:
                        new()
                    name = l[idx + len(START_TEXT):].strip()
                    lines = []
                    commands = []
                    continue

                idx = l.find(END_TEXT)
                if idx >= 0:
                    # end
                    if name:
                        new()
                    name = None
                    lines = []
                    commands = []
                    continue

                comment_body = striped[len(line_comment):].strip()
                if comment_body.startswith('{{') and comment_body.endswith('}}'):
                    # コマンド行
                    command_body = comment_body[2:-2].strip()
                    cidx = command_body.find(':')
                    if cidx == -1:
                        command_name = command_body
                        command_args = None
                    else:
                        command_name = command_body[:cidx].strip()
                        command_args = command_body[cidx+1:].strip()
                    commands.append((command_name, command_args))
                else:
                    # 通常コメント
                    lines.append(l)
            else:
                # 非コメント行
                lines.append(l)

    return sniplates


def walk(directory):
    for root, dirs, files in os.walk(directory):
        yield root
        for file in files:
            yield os.path.join(root, file)


def list_files(lang_name, lang_dir):
    ext = '.' + lang_name
    result = []
    for f in walk(lang_dir):
        if os.path.isfile(f) and f.endswith(ext):
            result.append(f)
    return result


def load_sniplates():
    '''
    設定ファイルで指定されたディレクトリから sniplate を読み込んでメモリ上に格納する
    '''
    settings = sublime.load_settings('Sniplate.sublime-settings')
    sniplate_dir = os.path.expanduser(settings.get('dir'))

    for lang_name in os.listdir(sniplate_dir):
        lang_dir = os.path.join(sniplate_dir, lang_name)
        if not os.path.isdir(lang_dir):
            continue

        lang_files = list_files(lang_name, lang_dir)

        if not lang_files:
            if lang_name in context:
                del context[lang_name]
            continue

        last = max(os.stat(fn).st_mtime for fn in lang_files)

        if lang_name in context:
            if context[lang_name].last >= last:
                continue

        lang = SniplateLang(lang_name, last)
        line_comment = line_comments[lang_name]

        sniplates = []
        for fn in lang_files:
            sniplates.extend(read_sniplates(fn, line_comment))

        if lang.build(sniplates):
            context[lang_name] = lang


def get_ext(filename):
    idx = filename.rfind('.')
    if idx < 0:
        return None
    else:
        return filename[idx + 1:]


def plugin_unloaded():
    global context
    context = {}


def load_at_command(view):
    load_sniplates()
    fn = view.file_name()
    ext = get_ext(fn)
    return context.get(ext)


class MyInsertCommand(sublime_plugin.TextCommand):
    '''
    最終的に view に文字列を挿入する処理
    '''
    def run(self, edit, characters):
        pos = self.view.sel()[0].a
        self.view.insert(edit, pos, characters)


class SniplateCommand(sublime_plugin.TextCommand):
    '''
    sniplate を選択して挿入する
    '''
    def run(self, edit):
        sniplates = load_at_command(self.view)
        items = sniplates.candidate_list

        def on_done(idx):
            if idx < 0:
                return
            sniplate = sniplates.sniplate_list[idx]
            self.view.run_command('sniplate_insert', {'name': sniplate.name})

        self.view.window().show_quick_panel(items, on_done)


class SniplateEditCommand(sublime_plugin.TextCommand):
    '''
    sniplate を選択して定義したファイルを開く
    '''
    def run(self, edit):
        sniplates = load_at_command(self.view)

        items = sniplates.candidate_list

        def on_done(idx):
            if idx < 0:
                return
            sniplate = sniplates.sniplate_list[idx]
            filename = sniplate.filename
            self.view.window().open_file(filename)

        self.view.window().show_quick_panel(items, on_done)


class SniplateInsertCommand(sublime_plugin.TextCommand):
    '''
    現在のカーソル位置に指定された sniplate を挿入する
    '''
    def run(self, edit, name):
        sniplates = load_at_command(self.view)
        sniplate = sniplates.sniplates.get(name)
        if not sniplate:
            return

        dic = sniplates.sniplates

        lines = []
        all_text = self.view.substr(sublime.Region(0, self.view.size()))
        inserted = set()

        def dfs(cur):
            '''
            DAG を辿りながら、挿入済みじゃないものを見つけて、lines に蓄える
            '''
            for req in cur.requires:
                dfs(dic[req])
            if cur.name in inserted or cur.pattern_line in all_text:
                return
            inserted.add(cur.name)
            lines.append(cur.pattern_line)
            lines.extend(cur.lines)
            lines.append('')

        dfs(sniplate)

        var_pattern = re.compile(r'{{\s*var\s*:\s*(\w+)\s*}}')

        var_names = set()

        for line in lines:
            m = var_pattern.search(line)
            if m:
                var_names.add(m.group(1))

        var_table = {}

        def rec():
            if var_names:
                var_name = var_names.pop()

                def on_done(input):
                    var_table[var_name] = input
                    rec()

                self.view.window().show_input_panel(var_name, '', on_done, None, None)
            else:
                insert_lines = []
                for line in lines:
                    m = var_pattern.search(line)
                    if m:
                        var_name = m.group(1)
                        if var_name in var_table:
                            newline = line[:m.start()] + var_table[var_name] + line[m.end():]
                            insert_lines.append(newline)
                        else:
                            insert_lines.append(line)
                    else:
                        insert_lines.append(line)

                self.view.run_command('my_insert', {'characters': '\n'.join(insert_lines)})
        rec()
