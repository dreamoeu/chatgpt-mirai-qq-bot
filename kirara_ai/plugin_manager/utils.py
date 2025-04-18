from importlib.metadata import PackageNotFoundError, distribution
from typing import Any, Dict, Optional


def get_package_metadata(package_name: str) -> Optional[Dict[str, Any]]:
    """获取Python包的元数据

    Args:
        package_name: 包名

    Returns:
        包含包元数据的字典，如果包不存在则返回None
    """
    try:
        dist = distribution(package_name)
        return {
            "name": dist.metadata["Name"],
            "version": dist.version,
            "description": dist.metadata["Summary"] if "Summary" in dist.metadata else "",
            "author": dist.metadata["Author"] if "Author" in dist.metadata else "",
        }
    except PackageNotFoundError:
        return None
