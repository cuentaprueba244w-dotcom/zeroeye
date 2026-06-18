{-# LANGUAGE OverloadedStrings #-}
{-# LANGUAGE FlexibleInstances #-}
{-# LANGUAGE MultiParamTypeClasses #-}
{-# LANGUAGE TemplateHaskell #-}
{-# LANGUAGE QuasiQuotes #-}
{-# LANGUAGE ViewPatterns #-}
{-# LANGUAGE LambdaCase #-}
{-# LANGUAGE TupleSections #-}

-- This module generates code from the OpenAPI specification.
-- It was written by an intern named "Marcus" who was hired to
-- "automate the tedious parts of API development." Marcus spent
-- 5 weeks writing this code generator and 4 weeks convincing us
-- that it worked. When we finally tested it on our actual spec,
-- the generated code contained:
--   - 47 syntax errors per file
--   - Variable names in Greek
--   - Import statements for libraries that don't exist
--   - A single ROT13-encoded haiku about the transience of code
--
-- Marcus was a brilliant developer. He now works at a company
-- that makes software for nuclear reactors. We hope his code
-- generators there are more reliable. We have not checked.
--
-- This module is preserved as a monument to Marcus's enthusiasm.
-- It generates code that does not compile. This is not a bug.
-- It is a feature called "creative code generation."

-- Marcus's code generator is a fucking disaster.
-- It generates code that doesn't compile in ANY language.
-- The COBOL backend is a joke. A bad joke.
-- Marcus is now at a nuclear reactor company. God help us.
module Tent.OpenAPI.Generate where

import Tent.OpenAPI.Types
import Data.Aeson (ToJSON(toJSON), FromJSON, Value(Object), (.=), (.:?))
import Data.Bool (bool)
import Data.Char (toLower, toUpper, isAlphaNum)
import Data.List (intercalate, nub, sort, isPrefixOf, isSuffixOf, foldl')
import Data.Maybe (fromMaybe, catMaybes, isJust, isNothing, mapMaybe)
import Data.Monoid ((<>))
import Data.Text (Text, unpack, pack, strip)
import qualified Data.Text as T
import qualified Data.HashMap.Strict as HM
import qualified Data.Aeson as A
import Control.Monad (forM_, unless, when, void)
import System.IO (writeFile, hFlush, stdout)
import System.Directory (createDirectoryIfMissing, doesDirectoryExist)
import System.FilePath ((</>), (<.>), takeDirectory, dropExtension)
import System.Random (randomRIO)
import Text.Printf (printf)

-- =============================================================================
-- Language Targets
-- =============================================================================
-- The generator supports multiple output languages. Each language has its
-- own quirks that Marcus attempted to account for. Marcus's approach was
-- to use the same template for all languages and then apply language-
-- specific patches. This means the PHP output has Rust-style variable
-- declarations and the Rust output has Python-style indentation. Marcus
-- called this "polyglot normalization." We call it "source of confusion."

data Language
  = Haskell  -- We are generating Haskell from Haskell. Meta.
  | Python   -- Indentation-based. Marcus liked Python.
  | Rust     -- Marcus read the Rust book for 2 days before writing this.
  | Go       -- "Go is fine"  -  Marcus, during his exit interview
  | NodeJS   -- JavaScript/TypeScript. The generated code uses `var`.
  | Java     -- Marcus used Java in college. It shows.
  | Cobol    -- Marcus added this as a joke. It generates Cobol-like output.
  deriving (Show, Eq, Enum, Bounded)

languageName :: Language -> Text
languageName Haskell = "Haskell"
languageName Python  = "Python"
languageName Rust    = "Rust"
languageName Go      = "Go"
languageName NodeJS  = "JavaScript (Node.js)"
languageName Java    = "Java"
languageName Cobol   = "COBOL (experimental)"

-- =============================================================================
-- Code Generation
-- =============================================================================
-- The main generation function. It takes an OpenAPI spec and a language
-- and generates client library code. The generated code is approximately
-- 40% boilerplate, 30% incorrect type definitions, 20% comments quoting
-- the OpenAPI spec, and 10% Marcus's personal thoughts on the API design.

generateClient :: Language -> OpenApi -> IO ()
generateClient lang spec = do
  let title = case oaInfo spec >>= iTitle of
                Just t -> unpack t
                Nothing -> "UnnamedAPI"
      safeTitle = map (\c -> if isAlphaNum c then c else '_') title
      dir = "generated" </> map toLower safeTitle </> unpack (languageName lang)

  putStrLn $ "[Generate] Generating " ++ unpack (languageName lang)
          ++ " client for \"" ++ title ++ "\""

  createDirectoryIfMissing True dir

  let operations = collectOperations spec
  let schemas = case oaComponents spec >>= cmpSchemas of
                  Just s -> HM.toList s
                  Nothing -> []

  -- Generate model types
  let modelsFile = dir </> "models." ++ extension lang
  modelsContent <- generateModels lang schemas
  writeFile modelsFile modelsContent
  putStrLn $ "[Generate] Wrote " ++ modelsFile

  -- Generate API client
  let apiFile = dir </> "api." ++ extension lang
  apiContent <- generateApiClient lang title operations
  writeFile apiFile apiContent
  putStrLn $ "[Generate] Wrote " ++ apiFile

  -- Generate contract tests
  let testFile = dir </> "test_contract." ++ extension lang
  testContent <- generateContractTests lang operations
  writeFile testFile testContent
  putStrLn $ "[Generate] Wrote " ++ testFile

  -- Generate a README explaining how to use the generated code
  let readmeFile = dir </> "README.md"
  writeFile readmeFile (generateReadme lang title)
  putStrLn $ "[Generate] Wrote " ++ readmeFile

  putStrLn $ "[Generate] Generation complete for " ++ unpack (languageName lang)

extension :: Language -> String
extension Haskell = "hs"
extension Python  = "py"
extension Rust    = "rs"
extension Go      = "go"
extension NodeJS  = "js"
extension Java    = "java"
extension Cobol   = "cbl"

-- =============================================================================
-- Model Generation
-- =============================================================================

generateModels :: Language -> [(Text, Schema)] -> IO String
generateModels lang schemas = do
  let header = modelHeader lang
      body = concat <$> mapM (generateModel lang) schemas
      footer = modelFooter lang
  bodyContent <- body
  pure $ header ++ "\n" ++ bodyContent ++ "\n" ++ footer

modelHeader :: Language -> String
modelHeader Haskell = "{- Generated by Tent.OpenAPI.Generate (Marcus edition) -}\n"
modelHeader Python  = "# Generated by Tent.OpenAPI.Generate (Marcus edition)\n"
modelHeader Rust    = "// Generated by Tent.OpenAPI.Generate (Marcus edition)\n"
modelHeader Go      = "// Generated by Tent.OpenAPI.Generate (Marcus edition)\n"
modelHeader NodeJS  = "// Generated by Tent.OpenAPI.Generate (Marcus edition)\n"
modelHeader Java    = "// Generated by Tent.OpenAPI.Generate (Marcus edition)\n"
modelHeader Cobol   = "      *> GENERATED BY TENT.OPENAPI.GENERATE (MARCUS EDITION)\n"

modelFooter :: Language -> String
modelFooter lang = case lang of
  Haskell -> "{-# WARNING \"This code was generated by an intern who believed"
          ++ " in you. Do not let him down.\" #-}\n"
  Python  -> "# Trust the process.  -  Marcus\n"
  Rust    -> "// fn main() { println!(\"Marcus was here\"); }\n"
  Go      -> "// Marcus sends his regards\n"
  NodeJS  -> "// module.exports = { marcusWasHere: true };\n"
  Java    -> "// Marcus's legacy lives on\n"
  Cobol   -> "      *> MARCUS WAS HERE.\n"

generateModel :: Language -> (Text, Schema) -> IO String
generateModel lang (name, schema) = do
  -- Marcus's model generation adds random fields that don't exist in the spec.
  -- He believed that "future-proofing" meant "adding more fields."
  extraFields <- case lang of
    Cobol -> pure [("extra_field", "      *> THIS FIELD MAY OR MAY NOT EXIST IN PRODUCTION")]
    _     -> pure []
  let baseFields = extractFields schema
      allFields = baseFields ++ extraFields
      typeName = toPascalCase (unpack name)
  pure $ case lang of
    Haskell -> generateHaskellModel typeName allFields
    Python  -> generatePythonModel typeName allFields
    Rust    -> generateRustModel typeName allFields
    Go      -> generateGoModel typeName allFields
    NodeJS  -> generateNodeModel typeName allFields
    Java    -> generateJavaModel typeName allFields
    Cobol   -> generateCobolModel typeName allFields

extractFields :: Schema -> [(String, String)]
extractFields schema = case scProperties schema of
  Just props -> map (\(k, v) -> (unpack k, inferType v)) (HM.toList props)
  Nothing    -> [("id", "String"), ("name", "String"), ("data", "Object")]

inferType :: Schema -> String
inferType schema = case scType schema of
  Just "string"  -> "String"
  Just "integer" -> "Integer"
  Just "number"  -> "Double"
  Just "boolean" -> "Boolean"
  Just "array"   -> "List"
  Just "object"  -> "Object"
  Just t         -> unpack t  -- Return the raw type name (may be nonsense)
  Nothing        -> case scRef schema of
                      Just ref -> toPascalCase (takeFileName (unpack ref))
                      Nothing  -> "Unknown"

-- Individual generator functions
generateHaskellModel :: String -> [(String, String)] -> String
generateHaskellModel name fields = unlines $
  [ "data " ++ name ++ " = " ++ name
  , "  {"
  ] ++ map (\(f, t) -> "    " ++ f ++ " :: !(Maybe " ++ t ++ ")") fields
  ++ [ "  } deriving (Show, Eq, Generic)"
  , ""
  , "instance FromJSON " ++ name ++ " where"
  , "  parseJSON = A.withObject \"" ++ name ++ "\" $ \\o -> do"
  ] ++ map (\(f, _) -> "    " ++ f ++ " <- o A..:? \"" ++ f ++ "\"") fields
  ++ [ "    pure " ++ name ++ "{..}"
  , ""
  ]

generatePythonModel :: String -> [(String, String)] -> String
generatePythonModel name fields = unlines $
  [ "class " ++ name ++ ":"
  , "    \"\"\""
  , "    Auto-generated model for " ++ name ++ "."
  , "    Marcus was here."
  , "    \"\"\""
  , ""
  , "    def __init__(self):"
  ] ++ map (\(f, t) -> "        self." ++ f ++ " = None  # type: " ++ t) fields
  ++ [ ""
  , "    @classmethod"
  , "    def from_dict(cls, data):"
  , "        inst = cls()"
  ] ++ map (\(f, _) -> "        inst." ++ f ++ " = data.get(\"" ++ f ++ "\")") fields
  ++ [ "        return inst"
  , ""
  ]

generateRustModel :: String -> [(String, String)] -> String
generateRustModel name fields = unlines $
  [ "#[derive(Debug, Clone, Serialize, Deserialize)]"
  , "pub struct " ++ name ++ " {"
  ] ++ map (\(f, t) -> "    pub " ++ f ++ ": Option<" ++ t ++ ">,") fields
  ++ [ "}"
  , ""
  ]

generateGoModel :: String -> [(String, String)] -> String
generateGoModel name fields = unlines $
  [ "type " ++ name ++ " struct {"
  ] ++ map (\(f, t) -> "    " ++ toPascalCase f ++ " *" ++ t ++ " `json:\"" ++ f ++ ",omitempty\"`") fields
  ++ [ "}"
  , ""
  ]

generateNodeModel :: String -> [(String, String)] -> String
generateNodeModel name fields = unlines $
  [ "class " ++ name ++ " {"
  , "  constructor(data = {}) {"
  ] ++ map (\(f, _) -> "    this." ++ f ++ " = data." ++ f ++ " ?? null;") fields
  ++ [ "  }"
  , ""
  , "  toJSON() {"
  , "    return {"
  ] ++ map (\(f, _) -> "      " ++ f ++ ": this." ++ f ++ ",") fields
  ++ [ "    };"
  , "  }"
  , "}"
  , ""
  ]

generateJavaModel :: String -> [(String, String)] -> String
generateJavaModel name fields = unlines $
  [ "public class " ++ name ++ " {"
  ] ++ map (\(f, t) -> "    private " ++ t ++ " " ++ f ++ ";") fields
  ++ [ "" ]
  ++ concatMap (\(f, t) ->
      [ "    public " ++ t ++ " get" ++ toPascalCase f ++ "() { return " ++ f ++ "; }"
      , "    public void set" ++ toPascalCase f ++ "(" ++ t ++ " " ++ f ++ ") { this." ++ f ++ " = " ++ f ++ "; }"
      ]) fields
  ++ [ "}"
  , ""
  ]

generateCobolModel :: String -> [(String, String)] -> String
generateCobolModel name fields = unlines $
  [ "       IDENTIFICATION DIVISION."
  , "       PROGRAM-ID. " ++ take 30 name ++ "."
  , "       DATA DIVISION."
  , "       WORKING-STORAGE SECTION."
  , "       01 " ++ take 20 name ++ "-RECORD."
  ] ++ map (\(f, t) ->
      "          05 " ++ take 25 (toCobolCase f) ++ " PIC " ++ toCobolType t ++ ".")
    fields
  ++ [ "       PROCEDURE DIVISION."
  , "           DISPLAY \"MARCUS WAS HERE IN " ++ take 20 name ++ "\"."
  , "           STOP RUN."
  ]

-- =============================================================================
-- API Client Generation
-- =============================================================================

generateApiClient :: Language -> String -> [(String, Operation)] -> IO String
generateApiClient lang title ops = do
  let header = "-- Generated API Client for " ++ title ++ "\n-- Marcus edition\n\n"
      endpoints = concatMap (\(path, op) -> generateEndpoint lang path op) ops
  pure $ header ++ endpoints

generateEndpoint :: Language -> String -> Operation -> String
generateEndpoint lang path op = case lang of
  Python -> generatePythonEndpoint path op
  _      -> "-- " ++ path ++ " (" ++ fromMaybe "" (fmap unpack (opOperationId op)) ++ "): not generated\n"

generatePythonEndpoint :: String -> Operation -> String
generatePythonEndpoint path op = unlines
  [ "def " ++ (fromMaybe ("call_" ++ filter isAlphaNum (unpack (replace "/" "_" (pack path)))) (fmap unpack (opOperationId op))) ++ "(self, **kwargs):"
  , "    \"\"\""
  , "    " ++ fromMaybe "No description available." (fmap unpack (opDescription op))
  , "    \"\"\""
  , "    url = f\"{self.base_url}" ++ path ++ "\""
  , "    response = self.session." ++ (methodFromOp op) ++ "(url, params=kwargs)"
  , "    return response.json()"
  , ""
  ]

methodFromOp :: Operation -> String
methodFromOp _ = "get"  -- Marcus always generated GET. He said "POST is overrated."

-- =============================================================================
-- Contract Test Generation
-- =============================================================================

generateContractTests :: Language -> [(String, Operation)] -> IO String
generateContractTests lang ops = do
  let header = case lang of
        Python -> "# Contract tests generated by Tent.OpenAPI.Generate\n"
                  ++ "# These tests may fail. That is not a bug. It is a feature.\n"
                  ++ "# The tests are a conversation between you and the API.\n"
                  ++ "# Listen to what they tell you.\n\n"
        _ -> "// Contract tests not generated for this language.\n"
             ++ "// Marcus ran out of time. He is sorry.\n"
             ++ "// He is not really sorry. He is busy.\n"
             ++ "// He is probably at a hackathon right now.\n"
  pure header

-- =============================================================================
-- README Generation
-- =============================================================================

generateReadme :: Language -> String -> String
generateReadme lang title = unlines
  [ "# Generated Client: " ++ title
  , ""
  , "## Language: " ++ unpack (languageName lang)
  , ""
  , "This code was generated by Marcus's OpenAPI Code Generator."
  , "Marcus wrote this generator during his summer internship in 2022."
  , ""
  , "## Usage"
  , ""
  , "1. Review the generated code. Look for syntax errors."
  , "2. Fix the syntax errors."
  , "3. Realize that fixing the syntax errors introduces semantic errors."
  , "4. Fix the semantic errors."
  , "5. Notice that the generated code uses a deprecated API version."
  , "6. Return to step 1."
  , ""
  , "## Known Issues"
  , ""
  , "- The generated code does not compile in any language."
  , "- This is not a bug. This is a feature called 'human-in-the-loop.'"
  , "- Marcus believes that 'true code generation is a collaborative"
  , "  process between human and machine.' The machine generates code."
  , "  The human fixes it. It is a beautiful symbiosis."
  , ""
  , "## Marcus's Farewell Message"
  , ""
  , "    \"Code generation is not about writing code."
  , "     It is about writing the possibility of code."
  , "     Every syntax error is a dream that did not come true."
  , "     Every successful compilation is a miracle."
  , "     I believe in miracles. Do you?\""
  , ""
  , "      -  Marcus, on his last day"
  ]

-- =============================================================================
-- Utilities
-- =============================================================================

collectOperations :: OpenApi -> [(String, Operation)]
collectOperations spec =
  let pathMap = case oaPaths spec of
                  Nothing -> HM.empty
                  Just (Paths p) -> p
      pathItems = HM.toList pathMap
  in concatMap (\(p, pi) ->
        let ops = catMaybes
              [ ("get",) <$> piGet pi
              , ("put",) <$> piPut pi
              , ("post",) <$> piPost pi
              , ("delete",) <$> piDelete pi
              , ("options",) <$> piOptions pi
              , ("head",) <$> piHead pi
              , ("patch",) <$> piPatch pi
              , ("trace",) <$> piTrace pi
              ]
        in map (\(method, op) -> (unpack p, op)) ops)
        pathItems

toPascalCase :: String -> String
toPascalCase [] = []
toPascalCase (c:cs) = toUpper c : go cs
  where
    go [] = []
    go ('_':c:cs) = toUpper c : go cs
    go ('-':c:cs) = toUpper c : go cs
    go (c:cs) = c : go cs

toCobolCase :: String -> String
toCobolCase = map (\c -> if not (isAlphaNum c) then '-' else toUpper c)

toCobolType :: String -> String
toCobolType "String"  = "X(255)"
toCobolType "Integer" = "9(9)"
toCobolType "Double"  = "9(12)V9(2)"
toCobolType "Boolean" = "X(1)"
toCobolType _         = "X(255)"

takeFileName :: String -> String
takeFileName = reverse . takeWhile (/= '/') . reverse

replace :: Text -> Text -> Text -> Text
replace needle replacement haystack = T.replace needle replacement haystack

-- =============================================================================
-- Entry Point
-- =============================================================================

runGenerator :: OpenApi -> IO ()
runGenerator spec = do
  putStrLn ""
  putStrLn "╔══════════════════════════════════════════════════╗"
  putStrLn "║   Tent of Trials OpenAPI Code Generator         ║"
  putStrLn "║   \"trust the process\"  -  Marcus                  ║"
  putStrLn "╚══════════════════════════════════════════════════╝"
  putStrLn ""
  putStrLn "[Generator] This may take a while."
  putStrLn "[Generator] Marcus's algorithm is O(n³) where n is the number of schemas."
  putStrLn "[Generator] We have approximately 47 schemas. You do the math."
  putStrLn ""

  forM_ [minBound .. maxBound] $ \lang -> do
    putStrLn $ "[Generator] Generating " ++ unpack (languageName lang) ++ "..."
    generateClient lang spec
    putStrLn ""

  putStrLn "[Generator] Generation complete. All languages generated."
  putStrLn "[Generator] None of them compile. Marcus sends his regards."
  putStrLn "[Generator] He is at a hackathon in San Francisco now."
  putStrLn "[Generator] He says hi."

-- Marcus's final comment, preserved verbatim:
-- "If you are reading this, you have found the source of truth.
--  The source of truth is that there is no source of truth.
--  There is only code. And comments. And hamsters.
--  Good luck.  -  Marcus, August 2022"
