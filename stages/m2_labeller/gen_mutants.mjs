// node gen_mutants.mjs REPO FILE... > mutants.json  -- enumerate single-point mutants (offsets are into the file text)
import { Project, SyntaxKind, Node } from "ts-morph";
import path from "node:path";
const root = path.resolve(process.argv[2]);
const project = new Project({ skipAddingFilesFromTsConfig: true, compilerOptions: { allowJs: false } });
const SWAP = { "===": "!==", "!==": "===", "==": "!=", "!=": "==", "<": ">=", ">": "<=", "<=": ">", ">=": "<", "&&": "||", "||": "&&", "??": "&&", "+": "-", "-": "+" };
const out = [];
for (const rel of process.argv.slice(3)) {
  const sf = project.addSourceFileAtPath(path.join(root, rel));
  const add = (mutator, node, repl, s = node.getStart(), e = node.getEnd()) => out.push({ file: rel, mutator, start: s, end: e, replacement: repl, line: sf.getLineAndColumnAtPos(s).line, original: sf.getFullText().slice(s, e).slice(0, 60) });
  const inType = (n) => n.getAncestors().some((a) => Node.isTypeNode(a) || Node.isInterfaceDeclaration(a) || Node.isTypeAliasDeclaration(a) || Node.isImportDeclaration(a) || Node.isExportDeclaration(a));
  sf.forEachDescendant((n) => {
    if (inType(n)) return;
    const k = n.getKind();
    if (k === SyntaxKind.BinaryExpression) { const op = n.getOperatorToken(); const r = SWAP[op.getText()]; if (r && !(op.getText() === "+" && n.getType?.().isString?.())) add("BinaryOp", op, r); }
    else if (k === SyntaxKind.TrueKeyword) add("Boolean", n, "false");
    else if (k === SyntaxKind.FalseKeyword) add("Boolean", n, "true");
    else if (k === SyntaxKind.PrefixUnaryExpression && n.getOperatorToken() === SyntaxKind.ExclamationToken) add("NegationRemoval", n, n.getOperand().getText());
    else if (k === SyntaxKind.IfStatement || k === SyntaxKind.ConditionalExpression) { const c = k === SyntaxKind.IfStatement ? n.getExpression() : n.getCondition(); add("CondTrue", c, "true"); add("CondFalse", c, "false"); }
    else if (k === SyntaxKind.ReturnStatement && n.getExpression()) add("ReturnUndefined", n.getExpression(), "undefined");
    else if (k === SyntaxKind.StringLiteral && n.getLiteralValue() !== "" && n.getParent().getKind() !== SyntaxKind.ImportDeclaration && n.getParent().getKind() !== SyntaxKind.ExportDeclaration) add("StringEmpty", n, '""');
    else if (k === SyntaxKind.Block && Node.isFunctionLikeDeclaration(n.getParent()) && n.getStatements().length) add("EmptyBody", n, "{}");
  });
}
process.stdout.write(JSON.stringify(out));
