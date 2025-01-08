import os
import streamlit as st
from lxml import etree

# Função para identificar o tipo de XML


def identify_xml_type(xml_root):
    namespace_map = {
        "http://www.portalfiscal.inf.br/cte": "CT-e",
        "http://www.portalfiscal.inf.br/nfe": "NF-e",
    }
    for ns, doc_type in namespace_map.items():
        if xml_root.tag.startswith(f"{{{ns}}}"):
            return doc_type
    return "Desconhecido"

# Função para validar um XML contra o XSD


def validate_xml(xml_content, xsd_file):
    try:
        # Carregar o schema principal
        schema_doc = etree.parse(xsd_file)
        schema = etree.XMLSchema(schema_doc)

        # Carregar o XML a partir do conteúdo
        xml_root = etree.fromstring(xml_content)

        # Validar o XML contra o schema
        schema.assertValid(xml_root)

        return True, None
    except etree.DocumentInvalid as e:
        return False, format_error_log(e.error_log, xml_content)
    except Exception as e:
        return False, str(e)

# Função para formatar os erros do validador


def format_error_log(error_log, xml_content):
    formatted_errors = []
    for error in error_log:
        field_name, field_value = extract_field_info(
            error.message, xml_content)
        formatted_errors.append(
            f"Linha {error.line}, coluna {error.column}: Coluna '{
                field_name}' com o valor '{field_value}' é inválida."
        )
    return "\n".join(formatted_errors)

# Função para extrair o nome do campo e o valor do erro


def extract_field_info(error_message, xml_content):
    field_name = "campo desconhecido"
    field_value = "valor não encontrado"

    if "{http://www.portalfiscal.inf.br/cte}" in error_message:
        start = error_message.find("{http://www.portalfiscal.inf.br/cte}")
        end = error_message.find("'", start)
        field_name = error_message[start +
                                   len("{http://www.portalfiscal.inf.br/cte}"):end]

        # Extrair o valor do campo do XML
        try:
            xml_root = etree.fromstring(xml_content)
            field_element = xml_root.find(
                f".//{{http://www.portalfiscal.inf.br/cte}}{field_name}")
            if field_element is not None and field_element.text:
                field_value = field_element.text.strip()
        except Exception:
            pass

    return field_name, field_value


# Caminho para os arquivos XSD
xsd_path = "validadores"
xsd_files = {
    "CT-e": os.path.join(xsd_path, "CT-e", "cte_v4.00.xsd"),
    "NF-e": os.path.join(xsd_path, "NF-e", "nfe_v4.00.xsd"),
}

# Configurar o Streamlit
st.title("Validador de XML para CT-e e NF-e")

# Upload de arquivos
uploaded_files = st.file_uploader(
    "Envie seus arquivos XML", accept_multiple_files=True, type=["xml"]
)

if uploaded_files:
    for uploaded_file in uploaded_files:
        st.write(f"### Arquivo: {uploaded_file.name}")

        try:
            # Ler o conteúdo do XML
            xml_content = uploaded_file.read()

            if not xml_content.strip():
                st.error("O arquivo está vazio!")
                continue

            # Carregar o XML
            xml_root = etree.fromstring(xml_content)

            # Identificar o tipo de XML
            xml_type = identify_xml_type(xml_root)
            st.write(f"Tipo de XML detectado: {xml_type}")

            # Validar o XML contra o schema correspondente
            xsd_file = xsd_files.get(xml_type)
            if not xsd_file:
                st.error("Tipo de XML não suportado ou schema não encontrado.")
                continue

            is_valid, errors = validate_xml(xml_content, xsd_file)
            if is_valid:
                st.success("XML válido de acordo com o schema.")
            else:
                st.error("XML inválido! Erros:")
                st.code(errors, language="plaintext")
        except etree.XMLSyntaxError as e:
            st.error(f"Erro de sintaxe no XML: {e}")
        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")
