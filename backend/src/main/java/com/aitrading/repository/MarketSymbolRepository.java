package com.aitrading.repository;

import com.aitrading.model.MarketSymbol;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface MarketSymbolRepository extends JpaRepository<MarketSymbol, Integer> {
    Optional<MarketSymbol> findBySymbolAndExchange(String symbol, String exchange);
    Optional<MarketSymbol> findBySymbol(String symbol);
}
