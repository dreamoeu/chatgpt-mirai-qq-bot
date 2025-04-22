from typing import Optional
from pydantic import BaseModel, field_validator

from .response import Usage

class LLMReRankRequest(BaseModel):
    """
    ReRanker: 重排器是一个重要的处理方案, 通常见于 EsSearch 的优化方案中。
    本接口是适用于 LLM 的重排器的请求模型一般与嵌入式式模型组合使用提高向量搜索准确率。

    传入一系列原始文档和一个查询语句，返回器相似度数值。
    Attributes:
        query: 原始查询语句
        documents: 文档列表, 包含文档的文本内容。每个文档转化为一个 string 类型传递。
        model: 重排模型的名称。为保证准确性，本实现将禁止自动选择模型。
        top_k: 返回最相似的 {top_k} 个文档。如果没有指定，将返回所有文档的重排序结果。
            Tips: 如果你决定不返回原始文档，那么不要设置这个选项。会丢失文本与相似度的关联。
        return_documents: 是否返回原始文档内容。注意如果你想要自动排序请将该字段设置为 True。
        truncation: 文档和查询语句是否允许被截断以适应模型最大上下文。
    """
    query: str
    documents: list[str]
    model: str
    top_k: Optional[int]
    return_documents: Optional[bool]
    truncation: Optional[bool]


class ReRankerContent(BaseModel):
    """
    ReRanker 的内容模型。

    Attributes:
        document: 原始文档内容。
        relevance_score: 文档的相似度分数。
    """

    document: Optional[str] = None
    relevance_score: float

class LLMReRankResponse(BaseModel):
    """
    ReRanker 的返回模型。

    Attributes:
        contents: 获取相似度分数后的文档。为了兼容选择不返回原始文档的情况。约定: 当且仅当return_documents为True时才启用排序。
        usage: token 使用情况。
    """

    contents: list[ReRankerContent]
    usage: Usage

    @field_validator("contents", mode="after")
    @classmethod
    def sort_content(cls, contents: list[ReRankerContent]) -> list[ReRankerContent]:
        if all(content.document is not None for content in contents):
            return sorted(contents, key= lambda x: x.relevance_score)
        else:
            return contents