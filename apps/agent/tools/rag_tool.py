"""LangChain tool wrapping regulatory RAG retrieval."""

from langchain_core.tools import tool
from sqlalchemy.ext.asyncio import AsyncSession

from rag.retriever import RegulatoryRetriever, chunks_to_context


_retriever = RegulatoryRetriever()


def create_regulatory_search_tool(session: AsyncSession | None = None):
    """Create a regulatory search tool bound to an optional DB session."""

    @tool
    async def search_regulatory_documents(
        query: str,
        product_category: str = "",
        hazard_type: str = "",
        source_body: str = "",
    ) -> str:
        """
        Search FSSAI, Codex, FDA, and ICMR regulatory documents for food safety
        information. Use for hazard analysis, critical limits, and compliance queries.

        Args:
            query: The search query describing what regulatory information is needed.
            product_category: Optional filter (e.g. 'dairy_pasteurized', 'rte', 'dairy').
            hazard_type: Optional filter ('biological', 'chemical', 'physical').
            source_body: Optional filter ('FSSAI', 'Codex', 'FDA', 'ICMR').
        """
        chunks = await _retriever.retrieve(
            session=session,
            query=query,
            source_body=source_body or None,
            product_category=product_category or None,
            hazard_type=hazard_type or None,
        )

        if not chunks:
            return (
                "No relevant regulatory documents found for this query. "
                "Please verify the product category or broaden the search terms."
            )

        header = f"Found {len(chunks)} relevant regulatory excerpts:\n\n"
        return header + chunks_to_context(chunks)

    return search_regulatory_documents
