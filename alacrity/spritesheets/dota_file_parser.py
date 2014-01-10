import argparse

def parse(filename):
    """Parses the file into a python dict"""
    result = {}
    cur_obj = result
    path = []
    with open(filename, 'rb') as f:
        descending = False
        for line_num,line in enumerate(f):
            line = line.strip()

            if line == '' or line.startswith('//'):
                continue
            tokens = line.split()

            def remove_comments(tokens):
                """Remove all tokens in a line that appear after a comment"""
                for token in tokens:
                    if token.startswith('//'):
                        tokens = tokens[:tokens.index(token)]
                        return tokens
                return tokens
            tokens = remove_comments(tokens)

            def combine_quoted(tokens):
                """Combine tokens that are within quotes but were split by whitespace"""
                quote_start_idx = None
                for token in tokens:
                    if token.count('"') % 2 == 1:
                        if quote_start_idx is None:
                            quote_start_idx = tokens.index(token)
                        else:
                            cur_idx = tokens.index(token)
                            tokens = tokens[:quote_start_idx] + [' '.join(tokens[quote_start_idx:cur_idx])]
                            return combine_quoted(tokens)
                return tokens
            tokens = combine_quoted(tokens)
            tokens = [x.strip('"') for x in tokens]

            # expected format: "key" "val"
            if len(tokens) == 2:
                key,val = tokens
                try:
                    val = int(val)
                except ValueError:
                    try:
                        val = float(val)
                    except ValueError:
                        pass
                cur_obj[key] = val
            # expected format: "{" OR "}" OR "key"
            elif len(tokens) == 1:
                if tokens[0] == "{":
                    path.append(cur_obj)
                    cur_obj[descending] = {}
                    cur_obj = cur_obj[descending]
                elif tokens[0] == "}":
                    cur_obj = path.pop()
                else:
                    descending = tokens[0]
            else:
                assert False, "Unexpected format for line {}: \n\tline: {}\n\ttokens: {}".format(line_num, line, tokens)

            # if line contains only closing brace, move cur_obj up a level
    return result

parsed = None
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('file',
            help='file to parse (e.g. "npc_heroes.txt" or "items.txt")')
    args = parser.parse_args()

    global parsed
    parsed = parse(args.file)


if __name__ == '__main__':
    main()
