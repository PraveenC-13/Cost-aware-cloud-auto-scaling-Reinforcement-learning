package com.hkbk.autoscaler;

import com.hkbk.autoscaler.model.AppConfig;
import com.hkbk.autoscaler.repository.AppConfigRepository;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;

@SpringBootApplication
public class AutoscalerApplication {

    public static void main(String[] args) {
        SpringApplication.run(AutoscalerApplication.class, args);
    }

    /** Make sure the singleton config row exists on first boot. */
    @Bean
    CommandLineRunner seedDefaultConfig(AppConfigRepository repository) {
        return args -> {
            if (repository.findById(AppConfig.SINGLETON_ID).isEmpty()) {
                repository.save(AppConfig.defaults());
            }
        };
    }
}
